
from __future__ import annotations

from dataclasses import dataclass
import itertools
import logging
from pathlib import Path
import sys
from typing import (
    Any, Collection, Container, Dict, FrozenSet, Iterable, Optional, Set,
    Tuple,
)

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from .command import Config
from .errors import Violation as V
from .errors import Warn, Warned, safe, unsafe
from .imports import find_source_files, get_external_modules
from .packages import canon, find_packages, get_preferred_name

logger = logging.getLogger()


def check_order(deps: Collection[str], label: str = 'dependencies') -> Iterable[Warn]:
    deps = list(deps)
    if not deps:
        return
    if deps[0] == 'python':
        deps = deps[1:]
    for first, second in zip(deps, itertools.islice(deps, 1, None)):
        if first.casefold() > second.casefold():
            yield V.ODEP006(f"{label} are not sorted: {first!r} before {second!r}")
            return

def fix_canonical_names(data: Dict[str, Any]) -> Warned[FrozenSet[str]]:
    def check_canon(package_name: str) -> Warned[str]:
        canonical_name = canon(package_name)
        if package_name != canonical_name:
            # The preferred name of the package (like "Django") might not be
            # the same as the canonical form ("django"). We allow the user to
            # specify either of the two, and warn for any other form.
            preferred_name = get_preferred_name(package_name) or canonical_name
            if package_name != preferred_name:
                return unsafe(
                    canonical_name,
                    V.ODEP007(f"dependency {package_name!r} is not the preferred name: consider {preferred_name!r}")
                )
        return safe(canonical_name)
    return Warned.gather(map(check_canon, data)).map(frozenset)

@dataclass(frozen=True)
class Project:
    dependencies: Collection[str]
    dev_dependencies: Collection[str]
    config: Config
    local_packages: FrozenSet[str] = frozenset()
    extra_paths: Tuple[Path, ...] = ()

    def check_dependencies(
        self, paths: Iterable[Path],
        *, exclude: Iterable[Path] = (),
    ) -> Iterable[Warn]:
        yield from self.check_modules(
            itertools.chain(paths, self.extra_paths),
            self.dependencies,
            self.local_packages,
            exclude=itertools.chain(exclude, self.config.local_test_paths),
        )

    def check_dev_dependencies(self, paths: Optional[Iterable[Path]]) -> Iterable[Warn]:
        yield from self.check_modules(
            itertools.chain(paths or (), self.config.local_test_paths),
            self.dev_dependencies,
            self.local_packages | set(self.config.local_test_packages),
            label='dev-dependencies',
            # Because dev-dependencies includes linters etc. that aren't used
            # anywhere in the code.
            check_unused=False,
        )

    def check_modules(
        self, paths: Iterable[Path], packages: Collection[str], local_packages: FrozenSet[str],
        *, label: str = 'dependencies', check_unused: bool = True, exclude: Iterable[Path] = (),
    ) -> Iterable[Warn]:
        paths = list(paths)
        logger.info(f"searching {', '.join(map(str, paths))}")
        def get_files(paths: Iterable[Path]) -> Set[Path]:
            return set(itertools.chain.from_iterable(map(find_source_files, paths)))
        included_paths = get_files(paths) - get_files(exclude)
        modules = [
            module for module in get_external_modules(included_paths)
            if not self.ignore_import(module)
        ]
        logger.info(f"{label} imported: {modules}")
        used: Set[str] = {'python'}
        for module in modules:
            founds = find_packages(module, local_packages)
            yield from founds.warnings
            found = list(map(canon, founds.value))
            if len(found) == 1:
                package = found[0]
                used.add(package)
                if package not in local_packages and not self.required(package, packages):
                    yield V.ODEP001(f"Package {package!r} is imported but not listed in {label}", package)
            elif len(found) == 0:
                yield V.ODEP002(f"Module {module!r} is imported but not installed, so I don't know what package is needed", module)
            else:
                # Namespace package - implemented across multiple installed
                # packages. So for any given import, we don't know which
                # package supplies that part of the namespace package.
                options = [pkg in local_packages or self.required(pkg, packages) for pkg in found]
                if all(options):
                    # OK, if we depend on them all that's fine
                    used.update(found)
                elif any(options):
                    yield V.ODEP003(f"Namespace package found: any of {found} might provide {module!r}")
                    used.update(found)
                else:
                    yield V.ODEP004(f"Namespace package found: any of {found} might provide {module!r}, and there are no dependencies on any of them", module)
        if check_unused:
            unused = set(packages) - used - set(self.config.ignore_dependencies)
            if unused:
                yield V.ODEP005(f"Unused {label} in project file: {sorted(unused)}")

    def ignore_import(self, module: str) -> bool:
        return bool(self.config) and module in self.config.ignore_imports

    def required(self, package: str, packages: Container[str]) -> bool:
        def mentioned(pkg: str) -> bool:
            return pkg in packages or pkg in self.local_packages
        if mentioned(package):
            return True
        for parent, children in self.config.child_packages.items():
            if package in children and mentioned(parent):
                return True
        return False

def read_poetry(toml_file: Optional[Path]) -> Warned[Project]:
    if toml_file is None:
        logger.error("pyproject.toml not specified")
        return safe(Project((), (), Config.make()))
    with toml_file.open('rb') as infile:
        tools = tomllib.load(infile)['tool']
    poetry_data = tools['poetry']
    config = Config.make(tools.get('omnidep'), toml_file)

    def process(deps: Dict[str, Any], *, dev: bool) -> Warned[FrozenSet[str]]:
        if dev:
            ignore = config.ignore_dev_dependencies_order
            key = 'dev-dependencies'
        else:
            ignore = config.ignore_dependencies_order
            key = 'dependencies'
        return (
            safe(deps)
            .collect(lambda x: () if ignore else check_order(x, key))
            .flatMap(fix_canonical_names)
        )

    deps = process(poetry_data['dependencies'], dev=False)
    # Poetry 1.2.0+ has two different places you can specify dev dependencies
    old_dev_data = poetry_data.get('dev-dependencies', {})
    old_dev_deps = process(old_dev_data, dev=True)
    new_dev_data = poetry_data.get('group', {}).get('dev', {}).get('dependencies', {})
    new_dev_deps = process(new_dev_data, dev=True)
    dev_deps: Warned[FrozenSet[str]] = (
        Warned.gather([old_dev_deps, new_dev_deps])
        .map(lambda x: frozenset(itertools.chain.from_iterable(x)))
    )

    pkgs = {pack['include'] for pack in poetry_data['packages']}
    project = Project(
        dependencies=deps.value,
        dev_dependencies=deps.value | dev_deps.value,
        config=config,
        local_packages=frozenset(map(canon, pkgs)),
        extra_paths=tuple(toml_file.parent / pack for pack in pkgs),
    )
    return Warned.gather([deps, dev_deps]).set(project)

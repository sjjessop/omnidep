
import collections
import contextlib
import functools
from importlib import metadata
from pathlib import Path
import re
import sys
from typing import FrozenSet, List, Mapping, Optional

from .errors import Violation as V
from .errors import Warned, safe, unsafe

punctuation = re.compile(r'[\-._]+')

# In Python 3.9+, should use functools.cache instead of lru_cache
# In Python 3.10+, there is metadata.packages_distributions, but all it checks
# is top_level.txt, so we still need to search for files as well.
@functools.lru_cache
def packages_distributions() -> Mapping[str, List[str]]:
    pkg_to_dist = collections.defaultdict(set)
    for dist in metadata.distributions():
        dist_name = dist.metadata['Name']
        def add_to(pkg: str) -> None:
            pkg_to_dist[pkg].add(dist_name)
        for toplevel in (dist.read_text('top_level.txt') or '').split():
            add_to(toplevel)
        for file in dist.files or ():
            # TODO - maybe the package could contain .pyc or .pyd but no .py
            if file.name == '__init__.py':
                add_to(str(file.parent))
            elif str(file.parent) == '.' and file.suffix == '.py':
                add_to(file.stem)
            else:
                add_to(file.parts[0])
    # TODO - make the return immutable, since it's cached
    return {key: sorted(value) for key, value in pkg_to_dist.items()}

def find_packages(module: str, local_packages: FrozenSet[str]) -> Warned[List[str]]:
    """
    Given a top-level code module, which installed package(s) provide it?
    This is a difficult question because Python packaging doesn't try to fully
    answer it, hence we need to apply some guesswork.
    """
    if canon(module) in local_packages:
        return safe([module])
    # TODO - Perhaps a more sure way would be to import the module and then
    # look for __file__ in all the packages.files
    #
    # If a package lists our module in its top-level.txt or sources, it will
    # appear here.
    package = packages_distributions().get(module)
    if package is not None:
        return safe(list(package))
    # Maybe the package is on the path, in which case no package dependency is
    # needed provided that it remains available on the path.
    if any((Path(path) / module).is_dir() for path in sys.path):
        return unsafe(
            [module],
            V.ODEP008(f"Module {module!r} not under package management but found on python path")
        )
    return safe([])

def canon(package_name: str) -> str:
    """
    Return the normalized name per PEP 503:
    https://peps.python.org/pep-0503/#normalized-names
    """
    return '-'.join(punctuation.split(package_name)).lower()

def get_preferred_name(package: str) -> Optional[str]:
    """
    Return the name the project calls itself.
    """
    # importlib_metadata.PackageNotFoundError inherits from FileNotFoundError
    # in old versions (<3) and ImportError more recently.
    with contextlib.suppress(FileNotFoundError, ImportError):
        name: Optional[str] = metadata.distribution(package).metadata['Name']
        return name
    return None

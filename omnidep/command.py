
from __future__ import annotations

import argparse
from dataclasses import dataclass, field, fields
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from .errors import ConfigError

# TODO - Python 3.11 will have public logging.getLevelNamesMapping
# https://github.com/python/cpython/issues/88024
# There is also a solution for click: https://pypi.org/project/click-loglevel/
log_levels = tuple(p[1] for p in sorted(logging._levelToName.items()))

# click and typer are good, but other lint tools like black and mypy depend on
# click (as does typer). Projects that want to use omnidep might also be using
# any past or future version of black/mypy/etc. I don't want to risk
# incompatibilities due to breaking changes in a common dependency, or do much
# work on an upgrade treadmill ensuring I always support every version of
# click. So, argparse it is.
parser = argparse.ArgumentParser(description="Check project dependencies against imports in code.")

CLT = TypeVar('CLT', bound='BasicCommandLine')

@dataclass
class BasicCommandLine:
    _log_level: Optional[str] = None
    verbose: bool = False

    @property
    def log_level(self) -> Optional[str]:
        if self.verbose:
            return 'INFO'
        return self._log_level

    @classmethod
    def parse(cls: Type[CLT], args: Optional[List[str]] = None) -> CLT:
        return parser.parse_args(args=args, namespace=cls())

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--log-level', choices=log_levels, dest='_log_level')
        parser.add_argument('--verbose', '-v', action='store_true', default=False)

@dataclass
class CommandLine(BasicCommandLine):
    paths: List[Path] = field(default_factory=list)
    project: Optional[Path] = None
    tests: Optional[List[Path]] = None

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('paths', metavar='PATH', nargs='+', type=Path)
        parser.add_argument('--project', metavar='PATH', type=Path)
        parser.add_argument('--tests', metavar='PATH', action='append', type=Path)
        super().add_arguments(parser)

CommandLine.add_arguments(parser)

@dataclass(frozen=True)
class Config:
    ignore_imports: List[str] = field(default_factory=list)
    child_packages: Dict[str, List[str]] = field(default_factory=dict)
    ignore_dependencies: List[str] = field(default_factory=list)
    local_test_packages: List[str] = field(default_factory=list)
    local_test_paths: List[Path] = field(default_factory=list)
    ignore_dependencies_order: bool = False
    ignore_dev_dependencies_order: bool = False

    @classmethod
    def make(cls, data: Optional[Dict[str, Any]] = None, toml_file: Optional[Path] = None) -> Config:
        data = data or {}
        allowed = {f.name: f for f in fields(cls)}
        args: Dict[str, Any] = {}
        for orig_key, value in data.items():
            key = orig_key.replace('-', '_')
            # Warn for typos or misunderstandings. Also rejects options from
            # future versions of the code. That's OK because the same project
            # file containing the options can require a version of omnidep that
            # supports them.
            if key not in allowed:
                raise ConfigError(f"Config option {orig_key!r} not recognised")
            convert: Dict[str, Callable[[Any], Any]] = {
                'List[Path]': lambda val: list(map(Path, val))
            }
            # It already is a str due to "import annotations". But mypy doesn't
            # seem to know that, so coerce it.
            expected_type = str(allowed[key].type)
            # Try to give a useful error message for misconfigurations.
            if not check_type[expected_type](value):
                raise ConfigError(f"Config option {orig_key!r}: expected {expected_type}, got {value!r}")
            converter = convert.get(expected_type, lambda x: x)
            args[key] = converter(value)
        if 'local_test_paths' in args and toml_file:
            new_paths = [toml_file.parent / path for path in args['local_test_paths']]
            args['local_test_paths'] = new_paths
        return Config(**args)

# Not many types needed, so just hack them rather than add a
# dependency on pydantic.
check_type: Dict[str, Callable[[object], bool]]
check_type = {
    'bool': lambda val: isinstance(val, bool),
    'List[str]': lambda val: (
        isinstance(val, list) and
        all(isinstance(x, str) for x in val)
    ),
    'List[Path]': lambda val: (
        isinstance(val, list) and
        all(isinstance(x, str) for x in val)
    ),
    'Dict[str, List[str]]': lambda val: (
        isinstance(val, dict) and
        all(isinstance(key, str) for key in val) and
        all(map(check_type['List[str]'], val.values()))
    ),
}

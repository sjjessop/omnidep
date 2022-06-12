
from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .errors import ConfigError

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
    def make(cls, data: Optional[Dict[str, Any]] = None) -> Config:
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
            # Try to give a useful error message for misconfigurations.
            # Not many types needed, so just hack them rather than add a
            # dependency on pydantic.
            check: Dict[str, Callable[[object], bool]]
            check = {
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
                    all(map(check['List[str]'], val.values()))
                ),
            }
            convert: Dict[str, Callable[[Any], Any]] = {
                'List[Path]': lambda val: list(map(Path, val))
            }
            # It already is a str due to "import annotations". But mypy doesn't
            # seem to know that, so coerce it.
            expected_type = str(allowed[key].type)
            if not check[expected_type](value):
                raise ConfigError(f"Config option {orig_key!r}: expected {expected_type}, got {value!r}")
            converter = convert.get(expected_type, lambda x: x)
            args[key] = converter(value)
        return Config(**args)

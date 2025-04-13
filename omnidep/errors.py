
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique
import itertools
from typing import Callable, Generic, Iterable, Optional, Tuple, TypeVar

class ConfigError(ValueError):
    pass

@unique
class Violation(Enum):
    # Might do a flake8 plugin some day, so use suitable codes
    ODEP001 = 'missing-dependency'
    ODEP002 = 'module-not-found'
    ODEP003 = 'namespace-used'
    ODEP004 = 'missing-namespace-dependency'
    ODEP005 = 'unused-dependency'
    ODEP006 = 'unsorted-dependency'
    ODEP007 = 'uncanonical-name'
    ODEP008 = 'unmanaged-module'

    def __call__(self, msg: str, package: Optional[str] = None) -> Warn:
        return Warn(self, msg, package)

@dataclass(frozen=True)
class Warn:
    code: Violation
    msg: str
    missing_package_name: Optional[str]

    @property
    def report(self) -> str:
        return f"{self.code.name}: {self.msg}"

T = TypeVar('T')
U = TypeVar('U')

@dataclass(frozen=True)
class Warned(Generic[T]):
    """
    Represents a value, plus zero or more warnings related to the generation of
    that value.

    This is more-or-less a Writer monad, where the semigroup (over which the
    written data is summed) is fixed as an iterable with concatenation.
    """
    value: T
    # TODO - tuple not efficient. Linked list?
    warnings: Tuple[Warn, ...] = ()

    def flatMap(self, func: Callable[[T], Warned[U]]) -> Warned[U]:
        """Change the value and append any number of warnings"""
        result = func(self.value)
        return Warned(result.value, self.warnings + result.warnings)
    def map(self, func: Callable[[T], U]) -> Warned[U]:
        """Change the value without changing the warnings"""
        return self.set(func(self.value))
    def collect(self, func: Callable[[T], Iterable[Warn]]) -> Warned[T]:
        """Append any number of warnings generated from the value, without changing the value"""
        return Warned(self.value, self.warnings + tuple(func(self.value)))

    def set(self, value: U) -> Warned[U]:
        """Set a new value without changing the warnings"""
        return Warned(value, self.warnings)

    def warn(self, warning: Warn) -> Warned[T]:
        """Append one warning without changing the value"""
        # This is like the function tell of cats.Writer
        return Warned(self.value, (*self.warnings, warning))
    def warnAll(self, warnings: Iterable[Warn]) -> Warned[T]:
        """Append any number of warnings without changing the value"""
        return Warned(self.value, self.warnings + tuple(warnings))

    def as_tuple(self) -> Tuple[T, Tuple[Warn, ...]]:
        """Return (value, warnings)"""
        return self.value, self.warnings
    @staticmethod
    def gather(items: Iterable[Warned[T]]) -> Warned[Tuple[T, ...]]:
        """
        Combine multiple Warned objects in the order specified.

        The values are placed into a tuple, and all warnings are concatenated.
        """
        # It's fine to read the iterable all at once, since zip will anyway.
        items = tuple(items)
        if len(items) == 0:
            # zip doesn't handle the case of no items.
            return Warned(())
        # map(Warned.as_tuple, items) works here, but mypy says no:
        # values, warningses = zip(*map(Warned.as_tuple, items))
        values, warningses = zip(*(item.as_tuple() for item in items))
        return Warned(values, tuple(itertools.chain.from_iterable(warningses)))

def safe(value: U) -> Warned[U]:
    """
    Convenience constructor: wraps value in Warned without any warnings.
    """
    return Warned(value)

def unsafe(value: U, *warnings: Warn) -> Warned[U]:
    """
    Convenience constructor: wraps value in Warned with 0 or more warnings.
    """
    return Warned(value, warnings)

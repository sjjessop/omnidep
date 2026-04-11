
# Import where we declare a dependency on a parent, not on this package.
import coverage  # noqa: F401
# TODO - shouldn't need this, but it prevents Violation.ODEP005: 'unused-dependency'
import pytest_cov  # type: ignore[import-untyped]  # noqa: F401

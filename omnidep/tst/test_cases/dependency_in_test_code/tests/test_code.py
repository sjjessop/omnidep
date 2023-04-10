
# Import something listed in dependencies: should not provoke an error, hence
# we test for two instances of ODEP001, not three.
import coverage  # noqa: F401
# Import something not listed in dependencies: will provoke error as long as
# this file is actually checked
import mypy  # noqa: F401
# Another not listed: hence we test for two instances of ODEP001, not one.
import pytest  # noqa: F401

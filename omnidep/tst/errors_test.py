
from typing import Callable, Iterable, Tuple

import pytest

from omnidep.errors import Violation, Warn, Warned, safe, unsafe

def assert_odep1(msg: str, warning: Warn) -> None:
    assert warning.code == Violation.ODEP001
    assert warning.msg == msg
    assert warning.missing_package_name is None
    assert warning.report == "ODEP001: " + msg

def test_violation() -> None:
    """Warnings are constructed from Violations"""
    warning = Violation.ODEP001("foo")
    assert_odep1("foo", warning)
    assert_odep1("bar", Violation.ODEP001("bar"))
    assert_odep1("baz", Violation.ODEP001("baz"))

def test_warned_constructor_1() -> None:
    """Single-arg constructor of Warned"""
    result = Warned(1)
    assert result.value == 1
    assert list(result.warnings) == []
    assert result.as_tuple() == (1, ())

def test_warned_constructor_2() -> None:
    """Two-arg constructor of Warned, with empty initial warnings"""
    result = Warned(2, ())
    assert result.value == 2
    assert list(result.warnings) == []
    assert result.as_tuple() == (2, ())

def test_warned_constructor_warnings() -> None:
    """Two-arg constructor of Warned, with a warning"""
    result = Warned(3, (Violation.ODEP001("foo"),))
    assert result.value == 3
    warnings = list(result.warnings)
    assert len(warnings) == 1
    assert_odep1("foo", warnings[0])
    assert result.as_tuple() == (3, (Violation.ODEP001("foo"),))

def test_warned_equality() -> None:
    """All the other tests will be based on equality, so it better be right."""
    def equal(m1: Warned[int], m2: Warned[int]) -> None:
        assert m1 == m2
        assert not m1 != m2
        assert m1.as_tuple() == m2.as_tuple()
        assert m1.value == m2.value
        assert list(m1.warnings) == list(m2.warnings)
    def notequal(m1: Warned[int], m2: Warned[int]) -> None:
        assert m1 != m2
        assert not m1 == m2
        assert m1.as_tuple() != m2.as_tuple()
        assert m1.value != m2.value or list(m1.warnings) != list(m2.warnings)
    for v in range(3):
        equal(Warned(v), Warned(v, ()))
    warns = [(), (warning1,), (warning1, warning2)]
    cases = [Warned(v, w) for v in range(3) for w in warns]
    for m in cases:
        equal(m, m)
    for left in range(len(cases)):
        for right in range(len(cases)):
            if left != right:
                notequal(cases[left], cases[right])

###########################
# Functions to test flatMap
###########################

def bad(x: int) -> Tuple[Warn, ...]:
    # Warning message depends on x value, so when we chain together to test
    # associativity we're asserting that the message order matches.
    return Violation.ODEP001(f"bad {x}"), Violation.ODEP001("and another thing")

def unit(x: int) -> Warned[int]:
    return Warned(x)
def unit_bad(x: int) -> Warned[int]:
    return Warned(x, bad(x))
def increment(x: int) -> Warned[int]:
    return Warned(x + 1)
def increment_bad(x: int) -> Warned[int]:
    return Warned(x + 1, bad(x))
def double(x: int) -> Warned[int]:
    return Warned(x * 2)
def double_bad(x: int) -> Warned[int]:
    return Warned(x * 2, bad(x))

all_funcs = [unit, unit_bad, increment, increment_bad, double, double_bad]
bad_funcs = [f for f in all_funcs if f.__name__.endswith('_bad')]
good_funcs = [f for f in all_funcs if not f.__name__.endswith('_bad')]
all_values = [0, 1, 2, 3, 19, 2**128 - 1]

IntFunc = Callable[[int], Warned[int]]


###########################################################
# flatMap applies the functions to produce expected results
###########################################################

@pytest.mark.parametrize('value', all_values)
@pytest.mark.parametrize('f', [unit, unit_bad])
def test_noop(value: int, f: IntFunc) -> None:
    assert Warned(value).flatMap(f).value == value

@pytest.mark.parametrize('value', all_values)
@pytest.mark.parametrize('f', [increment, increment_bad])
def test_increment(value: int, f: IntFunc) -> None:
    assert Warned(value).flatMap(f).value == value + 1

@pytest.mark.parametrize('value', all_values)
@pytest.mark.parametrize('f', [double, double_bad])
def test_double(value: int, f: IntFunc) -> None:
    assert Warned(value).flatMap(f).value == value * 2

@pytest.mark.parametrize('value', all_values)
@pytest.mark.parametrize('f', bad_funcs)
def test_msg(value: int, f: IntFunc) -> None:
    result = Warned(value).flatMap(f)
    assert list(result.warnings) == [*bad(value)]

@pytest.mark.parametrize('value', all_values)
@pytest.mark.parametrize('f', bad_funcs)
def test_msgs(value: int, f: IntFunc) -> None:
    result = Warned(value).flatMap(f).flatMap(f)
    second_value = f(value).value
    assert list(result.warnings) == [*bad(value), *bad(second_value)]

@pytest.mark.parametrize('value', all_values)
@pytest.mark.parametrize('f', good_funcs)
def test_no_msgs(value: int, f: IntFunc) -> None:
    result = Warned(value).flatMap(f)
    assert list(result.warnings) == []
    result = result.flatMap(f)
    assert list(result.warnings) == []
    result = result.flatMap(f)
    assert list(result.warnings) == []


############
# Monad laws
############

@pytest.mark.parametrize('value', all_values)
@pytest.mark.parametrize('f', all_funcs)
def test_monad_law_left(value: int, f: IntFunc) -> None:
    """
    Left-identity

    Applying unit, then flatmap, then f, is the same as just f.
    """
    assert Warned(value).flatMap(f) == f(value)

@pytest.mark.parametrize('value', all_values)
def test_monad_law_right(value: int) -> None:
    """
    Right-identity

    .flatMap(unit) does nothing.
    """
    for m in (Warned(value), Warned(value).flatMap(double_bad)):
        # Two ways of expressing the unit. We can't just say Warned because
        # it accepts anything and deduces type, hence has the wrong signature.
        for f in (unit, lambda x: Warned(x)):
            assert m.flatMap(f) == m

@pytest.mark.parametrize('value', all_values)
@pytest.mark.parametrize('f', all_funcs)
@pytest.mark.parametrize('g', all_funcs)
def test_monad_law_assoc(value: int, f: IntFunc, g: IntFunc) -> None:
    """
    Associativity

    flatMap f then g is the same as flatMap the composition.
    """
    for m in (Warned(value), Warned(value).flatMap(double_bad)):
        assert m.flatMap(f).flatMap(g) == m.flatMap(lambda x: f(x).flatMap(g))


####################################################
# gather(), which distributes Iterable across Warned
####################################################

def test_gather() -> None:
    warneds = [
        Warned(1),
        Warned(2).flatMap(double_bad),
        Warned(3).flatMap(double_bad).flatMap(double_bad),
    ]
    result: Warned[Tuple[int, ...]] = Warned.gather(iter(warneds))
    assert result.value == (1, 4, 12)
    assert list(result.warnings) == [*bad(2), *bad(3), *bad(6)]

def test_gather_empty() -> None:
    result: Warned[Tuple[int, ...]] = Warned.gather([])
    assert result.value == ()
    assert list(result.warnings) == []


##################################
# Additional convenience functions
#
# Each test has an assertion that
# defines the convenience function
# in terms of flatMap.
##################################

warning1 = Violation.ODEP001("one")
warning2 = Violation.ODEP002("two")
warning3 = Violation.ODEP003("three")

@pytest.mark.parametrize('value', all_values)
@pytest.mark.parametrize('f', all_funcs)
def test_map(value: int, f: IntFunc) -> None:
    """map() applies a "dropped" function that doesn't return Warned"""
    def g(x: int) -> int:
        return f(x).value
    result = Warned(value).map(g)
    assert result.value == Warned(value).flatMap(f).value
    assert result.value == g(value)
    assert list(result.warnings) == []
    for m in (Warned(value), Warned(value).map(g)):
        assert m.map(g) == m.flatMap(lambda x: Warned(g(x)))

@pytest.mark.parametrize('value', all_values)
def test_warn(value: int) -> None:
    """warn() adds a single warning"""
    result = Warned(value).warn(warning1).warn(warning2)
    assert result.value == value
    assert list(result.warnings) == [warning1, warning2]
    for m in (Warned(value), Warned(value).warn(warning1)):
        assert m.warn(warning2) == m.flatMap(lambda x: Warned(x, (warning2,)))

@pytest.mark.parametrize('value', all_values)
def test_warnAll(value: int) -> None:
    """warnAll() adds multiple warnings"""
    result = Warned(value).warnAll([warning1]).warnAll([warning2, warning3])
    assert result.value == value
    assert list(result.warnings) == [warning1, warning2, warning3]
    for m in (Warned(value), Warned(value).warnAll([warning1])):
        assert m.warnAll([warning2, warning3]) == m.flatMap(lambda x: Warned(x, (warning2, warning3)))

@pytest.mark.parametrize('value', all_values)
def test_collect(value: int) -> None:
    """
    collect() also adds multiple warnings, but they're generated from the
    current value.
    """
    def gen_warnings(value: int) -> Iterable[Warn]:
        return [*bad(value)]
    result = Warned(value).collect(gen_warnings)
    assert result.value == value
    assert list(result.warnings) == [*bad(value)]
    for m in (Warned(value), result):
        assert m.collect(gen_warnings) == m.flatMap(lambda x: Warned(x, tuple(gen_warnings(x))))

@pytest.mark.parametrize('x', all_values)
@pytest.mark.parametrize('y', all_values)
def test_set(x: int, y: int) -> None:
    """set() just changes the value"""
    assert Warned(x).set(y) == Warned(y)
    assert Warned(x, (warning1, warning2)).set(y) == Warned(y, (warning1, warning2))
    for m in (Warned(x), Warned(x, (warning1, warning2))):
        assert m.set(y) == m.flatMap(lambda x: Warned(y))


##########################
# Convenience constructors
##########################

# Use pre-existing values and functions to generate a mixture of monads with
# and without warnings included.
@pytest.mark.parametrize('value', all_values)
@pytest.mark.parametrize('f', [unit, unit_bad])
def test_safe(value: int, f: IntFunc) -> None:
    test_case = Warned(value).flatMap(f)
    assert safe(value) == Warned(value)
    one_warning = Violation.ODEP001("")
    assert unsafe(value, one_warning) == Warned(value, (one_warning,))
    assert unsafe(value, *test_case.warnings) == Warned(value, test_case.warnings)

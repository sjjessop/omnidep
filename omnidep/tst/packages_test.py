
from pathlib import Path
import sys

import pytest

from omnidep import packages

first_names = ('foo', 'Foo', 'FOO')
last_names = ('bar', 'Bar', 'BAR')
middle_bits = ('-', '_', '.', '__', '-_', '...')

@pytest.mark.parametrize('first', first_names)
@pytest.mark.parametrize('middle', middle_bits)
@pytest.mark.parametrize('last', last_names)
def test_canon(first: str, middle: str, last: str) -> None:
    assert packages.canon(first + middle + last) == 'foo-bar'

@pytest.mark.parametrize('first', first_names)
@pytest.mark.parametrize('middle', middle_bits)
@pytest.mark.parametrize('last', last_names)
@pytest.mark.parametrize('suffix', middle_bits)
def test_canon_suffix(first: str, middle: str, last: str, suffix: str) -> None:
    assert packages.canon(first + middle + last + suffix) == 'foo-bar-'

def test_get_preferred_name() -> None:
    assert packages.get_preferred_name('non-existent-package') is None
    assert packages.get_preferred_name('pytest') == 'pytest'
    assert packages.get_preferred_name('Pytest') == 'pytest'
    assert packages.get_preferred_name('PYTEST') == 'pytest'
    assert packages.get_preferred_name('pyOpenSSL') == 'pyOpenSSL'
    assert packages.get_preferred_name('pyopenssl') == 'pyOpenSSL'

def test_find_packages() -> None:
    local = frozenset({'omnidep'})

    # Non-existent package is found nowhere, represented by empty list
    result = packages.find_packages('non-existent-package', local)
    assert result.value == []
    assert result.warnings == ()

    # Installed package must be found
    result = packages.find_packages('omnidep', local)
    assert result.value == ['omnidep']
    assert result.warnings == ()

    # TODO - this is what currently happens, but it's wrong
    result = packages.find_packages('OmniDep', local)
    assert result.value == ['OmniDep']
    assert result.warnings == ()

    # Case where the imported name doesn't match the distributed name.
    # This is dev dependency only, although it'll be pulled in by all sorts.
    result = packages.find_packages('OpenSSL', local)
    assert result.value == ['pyOpenSSL']
    assert result.warnings == ()

    # Find packages on the path (with a warning)
    sys.path.append(str(Path(__file__).parent.parent))
    try:
        result = packages.find_packages('tst', frozenset())
        assert result.value == ['tst']
        assert len(result.warnings) == 1
    finally:
        sys.path.pop()
    # Check it wouldn't have been found without the path
    result = packages.find_packages('tst', frozenset())
    assert result.value == []
    assert result.warnings == ()

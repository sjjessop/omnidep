
from pathlib import Path
from unittest import mock

from omnidep import imports

test_dir = Path(__file__).parent

def test_find_source_files() -> None:
    results = list(imports.find_source_files(test_dir))
    assert Path(__file__) in results
    assert all(path.suffix == '.py' for path in results)

def test_is_external() -> None:
    assert not imports.is_external('pathlib')
    assert not imports.is_external('__future__')
    assert imports.is_external('omnidep')
    assert imports.is_external('pytest')
    # Not strictly true, but for our purposes
    assert not imports.is_external('setuptools')

def test_get_external_modules() -> None:
    results = imports.get_external_modules([test_dir])
    assert 'pathlib' not in results
    assert 'unittest' not in results
    assert 'omnidep' in results

def test_every_import() -> None:
    test_file = test_dir / 'test_cases' / 'every_import.py~'
    with mock.patch('omnidep.imports.find_source_files') as find:
        find.return_value = [test_file]
        results = list(imports.get_external_modules([Path('.')]))
    # Must not think 'bad' is a top-level import, in any place it occurs
    assert 'bad' not in results
    # Must find all the expected top-level imports, once each
    expected_results = sorted(f'example{x}' for x in range(1, 25))
    assert results == expected_results

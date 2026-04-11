
from pathlib import Path
from typing import Iterable, List, Tuple

import pytest

from omnidep import project
from omnidep.errors import Violation, Warn

test_dir = Path(__file__).parent
root_dir = test_dir.parent.parent

def test_no_toml(caplog: pytest.LogCaptureFixture) -> None:
    """Must handle case where toml file not specified"""
    assert project.read_pyproject(None).warnings == ()
    assert "pyproject.toml not specified" in caplog.text

def test_bad_toml() -> None:
    """Must handle case where toml file specified doesn't exist"""
    with pytest.raises(FileNotFoundError):
        project.read_pyproject(test_dir / 'no_such_pyproject.toml')

def test_self() -> None:
    """Must be able to load self as a project"""
    assert project.read_pyproject(root_dir / 'pyproject.toml').warnings == ()

Codes = List[Violation]

plain_project_files: List[Tuple[Path, Codes, Codes, Codes]] = [
    (test_dir / 'test_cases/unsorted_poetry', [Violation.ODEP006], [Violation.ODEP005], []),
    (test_dir / 'test_cases/unsorted_pep508', [Violation.ODEP006], [Violation.ODEP005], []),
    (test_dir / 'test_cases/case_sensitive_sorted_poetry', [Violation.ODEP006], [Violation.ODEP005], []),
    (test_dir / 'test_cases/case_sensitive_sorted_pep508', [Violation.ODEP006], [Violation.ODEP005], []),
    (test_dir / 'test_cases/case_insensitive_sorted_poetry', [], [Violation.ODEP005], []),
    (test_dir / 'test_cases/case_insensitive_sorted_pep508', [], [Violation.ODEP005], []),
    (test_dir / 'test_cases/dev_dependencies_old_poetry', [Violation.ODEP007], [], []),
    (test_dir / 'test_cases/dev_dependencies_new_poetry', [Violation.ODEP007], [], []),
    (test_dir / 'test_cases/dev_dependencies_pep508', [Violation.ODEP007], [], []),
    (test_dir / 'test_cases/dependency_in_test_code_poetry', [], [Violation.ODEP005], [Violation.ODEP001, Violation.ODEP001]),
    (test_dir / 'test_cases/dependency_in_test_code_pep508', [], [Violation.ODEP005], [Violation.ODEP001, Violation.ODEP001]),
    (test_dir / 'test_cases/failed_import_poetry', [], [Violation.ODEP002], []),
    (test_dir / 'test_cases/failed_import_pep508', [], [Violation.ODEP002], []),
    (test_dir / 'test_cases/failed_import_but_ignored_poetry', [], [], []),
    (test_dir / 'test_cases/failed_import_but_ignored_pep508', [], [], []),
    (test_dir / 'test_cases/namespace_none_declared_poetry', [], [Violation.ODEP004], []),
    (test_dir / 'test_cases/namespace_none_declared_pep508', [], [Violation.ODEP004], []),
    (test_dir / 'test_cases/namespace_one_declared_poetry', [], [Violation.ODEP003], []),
    (test_dir / 'test_cases/namespace_one_declared_pep508', [], [Violation.ODEP003], []),
    (test_dir / 'test_cases/namespace_three_declared_poetry', [], [], []),
    (test_dir / 'test_cases/namespace_three_declared_pep508', [], [], []),
    (test_dir / 'test_cases/parent_child_configured_poetry', [], [], []),
    (test_dir / 'test_cases/parent_child_configured_pep508', [], [], []),
    (test_dir / 'test_cases/parent_child_misconfigured_poetry', [], [Violation.ODEP001], []),
    (test_dir / 'test_cases/parent_child_misconfigured_pep508', [], [Violation.ODEP001], []),
    (test_dir / 'test_cases/test_filter_missed_poetry', [], [Violation.ODEP001], []),
    (test_dir / 'test_cases/test_filter_missed_pep508', [], [Violation.ODEP001], []),
    (test_dir / 'test_cases/test_filter_hit_poetry', [], [], []),
    (test_dir / 'test_cases/test_filter_hit_pep508', [], [], []),
]

def codes(warnings: Iterable[Warn]) -> Codes:
    return [warning.code for warning in warnings]

@pytest.mark.parametrize('projdir,expected,main,dev', plain_project_files)
def test_known_project_files(projdir: Path, expected: Codes, main: Codes, dev: Codes) -> None:
    """
    Must generate the expected warnings from known pyproject.toml files
    """
    result = project.read_pyproject(projdir / 'pyproject.toml')
    assert codes(result.warnings) == expected
    assert codes(result.value.check_dependencies([])) == main
    assert codes(result.value.check_dev_dependencies([])) == dev
    assert codes(result.value.check_dev_dependencies(None)) == dev

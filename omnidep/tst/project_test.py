
from pathlib import Path
from typing import Iterable, List, Tuple

import pytest

from omnidep import project
from omnidep.errors import Violation, Warn

test_dir = Path(__file__).parent
root_dir = test_dir.parent.parent

def test_no_toml(caplog: pytest.LogCaptureFixture) -> None:
    """Must handle case where toml file not specified"""
    assert project.read_poetry(None).warnings == ()
    assert "pyproject.toml not specified" in caplog.text

def test_bad_toml() -> None:
    """Must handle case where toml file specified doesn't exist"""
    with pytest.raises(FileNotFoundError):
        project.read_poetry(test_dir / 'no_such_pyproject.toml')

def test_self() -> None:
    """Must be able to load self as a project"""
    assert project.read_poetry(root_dir / 'pyproject.toml').warnings == ()

Codes = List[Violation]

plain_project_files: List[Tuple[Path, Codes, Codes, Codes]] = [
    (test_dir / 'test_cases/unsorted', [Violation.ODEP006], [Violation.ODEP005], []),
    (test_dir / 'test_cases/case_sensitive_sorted', [Violation.ODEP006], [Violation.ODEP005], []),
    (test_dir / 'test_cases/case_insensitive_sorted', [], [Violation.ODEP005], []),
    (test_dir / 'test_cases/dev_dependencies_old', [Violation.ODEP007], [], []),
    (test_dir / 'test_cases/dev_dependencies_new', [Violation.ODEP007], [], []),
    (test_dir / 'test_cases/dependency_in_test_code', [], [Violation.ODEP005], [Violation.ODEP001, Violation.ODEP001]),
    (test_dir / 'test_cases/failed_import', [], [Violation.ODEP002], []),
    (test_dir / 'test_cases/failed_import_but_ignored', [], [], []),
    (test_dir / 'test_cases/namespace_none_declared', [], [Violation.ODEP004], []),
    (test_dir / 'test_cases/namespace_one_declared', [], [Violation.ODEP003], []),
    (test_dir / 'test_cases/namespace_three_declared', [], [], []),
    (test_dir / 'test_cases/parent_child_configured', [], [], []),
    (test_dir / 'test_cases/parent_child_misconfigured', [], [Violation.ODEP001], []),
    (test_dir / 'test_cases/test_filter_missed', [], [Violation.ODEP001], []),
    (test_dir / 'test_cases/test_filter_hit', [], [], []),
]

def codes(warnings: Iterable[Warn]) -> Codes:
    return [warning.code for warning in warnings]

@pytest.mark.parametrize('projdir,expected,main,dev', plain_project_files)
def test_known_project_files(projdir: Path, expected: Codes, main: Codes, dev: Codes) -> None:
    """
    Must generate the expected warnings from known pyproject.toml files
    """
    result = project.read_poetry(projdir / 'pyproject.toml')
    assert codes(result.warnings) == expected
    assert codes(result.value.check_dependencies([])) == main
    assert codes(result.value.check_dev_dependencies([])) == dev
    assert codes(result.value.check_dev_dependencies(None)) == dev


from pathlib import Path
from typing import Iterable, List, Tuple

import pytest

from omnidep import project
from omnidep.errors import Violation, Warn

test_dir = Path(__file__).parent
root_dir = test_dir.parent.parent

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
    (test_dir / 'test_cases/dependency_in_test_code', [], [], [Violation.ODEP001]),
]

def codes(warnings: Iterable[Warn]) -> Codes:
    return [warning.code for warning in warnings]

@pytest.mark.parametrize('projdir,expected,main,dev', plain_project_files)
def test_known_project_files(projdir: Path, expected: Codes, main: Codes, dev: Codes) -> None:
    """
    Must generate the expected warnings from known pyproject.toml files

    These test cases don't include any source code, just the toml.
    """
    result = project.read_poetry(projdir / 'pyproject.toml')
    assert codes(result.warnings) == expected
    assert codes(result.value.check_dependencies([])) == main
    assert codes(result.value.check_dev_dependencies([])) == dev
    assert codes(result.value.check_dev_dependencies(None)) == dev

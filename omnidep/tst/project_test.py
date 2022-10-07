
from pathlib import Path
from typing import List

import pytest

from omnidep import project
from omnidep.errors import Violation

test_dir = Path(__file__).parent
root_dir = test_dir.parent.parent

def test_self() -> None:
    """Must be able to load self as a project"""
    assert project.read_poetry(root_dir / 'pyproject.toml').warnings == ()


plain_project_files = [
    (test_dir / 'test_cases/unsorted', [Violation.ODEP006]),
    (test_dir / 'test_cases/case_sensitive_sorted', [Violation.ODEP006]),
    (test_dir / 'test_cases/case_insensitive_sorted', []),
]

@pytest.mark.parametrize('dir,expected', plain_project_files)
def test_known_project_files(dir: Path, expected: List[Violation]) -> None:
    """
    Must generate the expected warnings from known pyproject.toml files

    These test cases don't include any source code, just the toml.
    """
    warnings = project.read_poetry(dir / 'pyproject.toml').warnings
    assert [warning.code for warning in warnings] == expected

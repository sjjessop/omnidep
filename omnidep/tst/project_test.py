
from pathlib import Path

from omnidep import project

test_dir = Path(__file__).parent
root_dir = test_dir.parent.parent

def test_self() -> None:
    """Must be able to load self as a project"""
    assert project.read_poetry(root_dir / 'pyproject.toml').warnings == ()

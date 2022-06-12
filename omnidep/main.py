
import enum
import logging
from pathlib import Path
from typing import Iterable, List, Optional

import typer

from .errors import ConfigError
from .project import read_poetry

logger = logging.getLogger()


def get_project_file(paths: Iterable[Path]) -> Optional[Path]:
    tomls = set(path for path in paths if path.name == 'pyproject.toml')
    if len(tomls) > 1:
        raise SystemExit("ERROR: Multiple pyproject.toml files specified")
    if len(tomls) == 1:
        return tomls.pop()
    return None

# TODO - Python 3.11 will have public logging.getLevelNamesMapping
# https://bugs.python.org/issue43858
# There is also a solution for click: https://pypi.org/project/click-loglevel/
log_levels = tuple(p[1] for p in sorted(logging._levelToName.items()))
LogLevel = enum.Enum('LogLevel', {x: x for x in log_levels})  # type: ignore

def main(
    paths: List[Path],
    project: Optional[Path] = typer.Option(None),
    tests: Optional[List[Path]] = typer.Option(None),
    log_level: Optional[LogLevel] = typer.Option('WARNING'),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    if verbose:
        log_level = LogLevel['INFO']
    if log_level is not None:
        logging.basicConfig(level=log_level.value)

    warnings = (
        read_poetry(project or get_project_file(paths))
        .collect(lambda x: x.check_dependencies(paths, exclude=tests or ()))
        .collect(lambda x: x.check_dev_dependencies(tests))
    ).warnings

    if warnings:
        print('\n'.join(w.report for w in warnings))
    bad = set(filter(None, (x.missing_package_name for x in warnings)))
    if bad:
        word = "package" if len(bad) == 1 else "packages"
        logger.error(f"""
            {len(bad)} missing {word}: {sorted(bad)}.
            Indirect dependencies may provide the packages you need, but can't specify what version you rely on.
            Therefore breaking changes in future versions could be introduced via the intermediate dependency.
            Solutions:
            * List the package name as an explicit dependency.
            * To assume that a dependency on X also provides Y, add X = ["Y"] to "child-packages".
            * To ignore an imported module name, add it to "ignore-imports".
        """.replace('    ', ' '))
        raise SystemExit(1)

def script_entry_point() -> None:
    try:
        typer.run(main)
    except ConfigError as e:
        raise SystemExit(str(e))
    finally:
        print("")

if __name__ == '__main__':
    script_entry_point()

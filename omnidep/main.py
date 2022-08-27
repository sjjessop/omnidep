#!/usr/bin/env python3
#

import logging
from pathlib import Path
from typing import Iterable, Optional

from .command import CommandLine
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

def main(args: CommandLine) -> None:
    warnings = (
        read_poetry(args.project or get_project_file(args.paths))
        .collect(lambda x: x.check_dependencies(args.paths, exclude=args.tests or ()))
        .collect(lambda x: x.check_dev_dependencies(args.tests))
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
    else:
        logger.info("No issues found")

def script_entry_point() -> None:
    args = CommandLine.parse()
    if args.log_level is not None:
        logging.basicConfig(level=args.log_level)
    try:
        main(args)
    except ConfigError as e:
        raise SystemExit(str(e))
    finally:
        print("")

if __name__ == '__main__':
    script_entry_point()

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
        print("See https://github.com/sjjessop/omnidep#error-codes-explained")
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

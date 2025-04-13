
import ast
import itertools
from pathlib import Path
import sys
from typing import Iterable, List

basic_types = (str, float, int, bytes, type(...))

def iter_import_names(tree: ast.AST) -> Iterable[str]:
    to_process: List[object] = [tree]
    while to_process:
        node = to_process.pop()
        if isinstance(node, ast.ImportFrom):
            # print(ast.unparse(node))
            if node.level == 0 and node.module is not None:
                yield node.module.partition('.')[0]
        elif isinstance(node, ast.Import):
            # print(ast.unparse(node))
            for alias in node.names:
                yield alias.name.partition('.')[0]
        elif node is None:
            pass
        elif isinstance(node, list):
            to_process.extend(node)
        elif isinstance(node, ast.AST):
            to_process.extend(getattr(node, name) for name in node._fields)
        elif not isinstance(node, basic_types):
            raise NotImplementedError(f"unhandled {type(node)} {node!r}")

def find_source_files(path: Path) -> Iterable[Path]:
    if '*' not in path.name and path.parent.name != '**':
        if path.is_file() and path.suffix == '.py':
            return [path]
        if path.is_dir():
            return path.rglob('*.py')
        # Doesn't exist, and not a glob, so no matches
        return []
    pattern = path.name
    parent = path.parent
    if parent.name == '**':
        matches = parent.parent.rglob(pattern)
    else:
        matches = parent.glob(pattern)
    return [match for match in matches if match.suffix == '.py']

def iter_modules(path: Path) -> Iterable[str]:
    for file in find_source_files(path):
        with file.open(encoding='utf8') as infile:
            # print(file)
            tree = ast.parse(infile.read())
            yield from iter_import_names(tree)

def is_external(module: str) -> bool:
    if module in ('setuptools', 'pkg_resources'):
        # Debateable: not technically part of Python, but distributed with it.
        return False
    if sys.version_info >= (3, 10):
        if module == '__future__':
            return False
        return module not in sys.stdlib_module_names
    else:  # noqa: RET505 # disagrees with mypy
        # Older Python
        from isort import place_module
        return str(place_module(module)) not in ('STDLIB', 'FUTURE')

def get_external_modules(paths: Iterable[Path]) -> List[str]:
    all_modules = itertools.chain.from_iterable(map(iter_modules, paths))
    return sorted(set(filter(is_external, all_modules)))

"""AST注释删除工具 - 删除Python文件中的所有注释和docstring。

支持作为通用工具使用，可通过命令行或函数调用。
"""

import ast
import sys
from pathlib import Path


def delete_comments(input_file: str, output_file: str) -> None:
    """删除Python文件中的所有注释和docstring。

    使用AST解析源代码，重建时不包含注释和文档字符串。

    Args:
        input_file: 输入Python文件路径
        output_file: 输出文件路径（无注释版本）

    Raises:
        FileNotFoundError: 输入文件不存在
        SyntaxError: 输入文件语法错误
    """
    input_path: Path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f'输入文件不存在: {input_file}')

    # 读取源代码
    source: str = input_path.read_text(encoding='utf-8')

    # 解析AST
    try:
        tree: ast.Module = ast.parse(source)
    except SyntaxError as e:
        raise SyntaxError(f'解析失败: {e}')

    # 删除所有docstring
    for node in ast.walk(tree):
        # 删除函数、类、模块的docstring
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                node.body.pop(0)
        # 删除类型注解中的字符串（如TypeVar的docstring）
        if isinstance(node, ast.AnnAssign):
            if hasattr(node, 'simple'):
                node.simple = 1  # type: ignore

    # 使用ast.unparse重建代码（Python 3.9+）
    try:
        new_source: str = ast.unparse(tree)
    except AttributeError:
        raise RuntimeError('Python 3.9+ 需要ast.unparse支持')

    # 写入输出文件
    output_path: Path = Path(output_file)
    output_path.write_text(new_source, encoding='utf-8')


def main() -> int:
    """命令行入口。

    Returns:
        int: 退出码，0表示成功
    """
    if len(sys.argv) < 2:
        print('用法: python comment_deleter.py <输入文件> [输出文件]')
        print('示例: python comment_deleter.py input.py output.py')
        return 1

    input_file: str = sys.argv[1]

    # 默认输出文件名为 input_clean.py
    if len(sys.argv) >= 3:
        output_file: str = sys.argv[2]
    else:
        input_path: Path = Path(input_file)
        output_file = str(input_path.parent / f'{input_path.stem}_clean{input_path.suffix}')

    try:
        delete_comments(input_file, output_file)
        print(f'已删除注释: {input_file} -> {output_file}')
        return 0
    except FileNotFoundError as e:
        print(f'错误: {e}')
        return 1
    except SyntaxError as e:
        print(f'错误: {e}')
        return 1
    except Exception as e:
        print(f'错误: {e}')
        return 1


if __name__ == '__main__':
    sys.exit(main())

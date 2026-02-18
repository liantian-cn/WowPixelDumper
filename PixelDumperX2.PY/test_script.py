"""测试脚本 - 验证重构后的模块功能。"""

import numpy as np
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def test_utils() -> bool:
    """测试Utils模块。"""
    print('=== 测试 Utils.py ===')
    try:
        from Utils import app_dir, load_template, find_all_matches

        # 测试 app_dir
        print(f'app_dir: {app_dir}')
        assert app_dir.exists(), 'app_dir 不存在'

        # 测试 load_template
        template_path = app_dir / 'mark8.png'
        if template_path.exists():
            template = load_template(str(template_path))
            print(f'模板加载成功: {template.shape}')
            assert template.shape[2] == 3, '模板应为RGB格式'
        else:
            print('警告: mark8.png 不存在，跳过模板测试')

        print('Utils.py 测试通过\\n')
        return True
    except Exception as e:
        print(f'Utils.py 测试失败: {e}\\n')
        return False


def test_database() -> bool:
    """测试Database模块。"""
    print('=== 测试 Database.py ===')
    try:
        from Database import NodeTitleManager, TitleRecord, cosine_similarity

        # 测试余弦相似度
        a = np.ones((6, 6, 3), dtype=np.uint8) * 255
        b = np.ones((6, 6, 3), dtype=np.uint8) * 255
        sim = cosine_similarity(a, b)
        print(f'相同数组余弦相似度: {sim}')
        assert sim > 0.99, '相同数组相似度应接近1'

        # 测试数据库（使用临时数据库）
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            manager = NodeTitleManager(db_path=db_path, similarity_threshold=0.95)
            print(f'数据库初始化成功: {db_path}')

            # 测试添加记录
            full_array = np.random.randint(0, 256, (8, 8, 3), dtype=np.uint8)
            middle_array = full_array[1:7, 1:7]
            import xxhash
            middle_hash = xxhash.xxh3_64_hexdigest(
                np.ascontiguousarray(middle_array), seed=0
            )

            record_id = manager.add_title(
                full_array=full_array,
                middle_hash=middle_hash,
                middle_array=middle_array,
                title='TestSpell',
                match_type='manual'
            )
            print(f'添加记录成功，ID: {record_id}')

            # 测试获取标题
            title = manager.get_title(
                middle_hash=middle_hash,
                middle_array=middle_array,
                full_array=full_array
            )
            print(f'获取标题: {title}')
            assert title == 'TestSpell', '标题应匹配'

            # 测试统计
            stats = manager.get_stats()
            print(f'统计数据: {stats}')

            # 测试获取所有记录
            records = manager.get_all_titles()
            print(f'记录数量: {len(records)}')
            assert len(records) == 1, '应有1条记录'

        finally:
            # 清理临时数据库
            if os.path.exists(db_path):
                os.remove(db_path)

        print('Database.py 测试通过\\n')
        return True
    except Exception as e:
        print(f'Database.py 测试失败: {e}\\n')
        import traceback
        traceback.print_exc()
        return False


def test_node() -> bool:
    """测试Node模块。"""
    print('=== 测试 Node.py ===')
    try:
        from Node import Node, NodeExtractor

        # 测试 Node
        # 创建纯色黑色节点
        black_array = np.zeros((8, 8, 3), dtype=np.uint8)
        node = Node(0, 0, black_array)

        assert node.is_pure, '黑色应为纯色'
        assert node.is_black, '应为黑色节点'
        assert not node.is_white, '不应为白色'
        assert node.color == (0, 0, 0), '颜色应为(0,0,0)'

        # 测试 NodeExtractor
        # 创建更大的数组用于提取器
        large_array = np.zeros((64, 64, 3), dtype=np.uint8)
        extractor = NodeExtractor(large_array)

        # 获取节点
        extracted_node = extractor.node(0, 0)
        assert extracted_node.is_pure, '提取的节点应为纯色'
        assert extracted_node.is_black, '提取的节点应为黑色'

        print('Node.py 测试通过\\n')
        return True
    except Exception as e:
        print(f'Node.py 测试失败: {e}\\n')
        import traceback
        traceback.print_exc()
        return False


def test_comment_deleter() -> bool:
    """测试comment_deleter模块。"""
    print('=== 测试 comment_deleter.py ===')
    try:
        from comment_deleter import delete_comments
        import tempfile
        import os

        # 创建测试文件
        test_code = '''"""模块文档字符串。"""
import os

def func():
    """函数文档字符串。"""
    # 行内注释
    x = 1  # 另一个注释
    return x

# 独立注释
class MyClass:
    """类文档字符串。"""
    pass
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            input_path = f.name

        output_path = input_path.replace('.py', '_clean.py')

        try:
            delete_comments(input_path, output_path)

            # 读取结果
            with open(output_path, 'r') as f:
                result = f.read()

            print(f'删除注释后的代码:\\n{result}')

            # 验证注释已删除
            assert '"""' not in result, '文档字符串应被删除'
            assert '#' not in result, '行内注释应被删除'

        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)

        print('comment_deleter.py 测试通过\\n')
        return True
    except Exception as e:
        print(f'comment_deleter.py 测试失败: {e}\\n')
        import traceback
        traceback.print_exc()
        return False


def main() -> int:
    """运行所有测试。

    Returns:
        int: 0表示全部通过，1表示有失败
    """
    print('开始测试 PixelDumper 重构模块...\\n')

    results = []

    results.append(('Utils', test_utils()))
    results.append(('Database', test_database()))
    results.append(('Node', test_node()))
    results.append(('comment_deleter', test_comment_deleter()))

    print('=== 测试结果汇总 ===')
    all_passed = True
    for name, passed in results:
        status = '通过' if passed else '失败'
        print(f'{name}: {status}')
        if not passed:
            all_passed = False

    if all_passed:
        print('\\n所有测试通过！')
        return 0
    else:
        print('\\n部分测试失败。')
        return 1


if __name__ == '__main__':
    sys.exit(main())

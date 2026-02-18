"""节点标题管理器 - 管理Node图标标题数据库，提供hash匹配、余弦相似度匹配。"""

import base64
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from Utils import app_dir, _ColorMap


def calculate_footnote_title(full_array: np.ndarray) -> str:
    """计算 footnote_title (右下2x2像素区域的类型)。

    Args:
        full_array: 8x8x3 numpy数组

    Returns:
        str: 如果footnote是纯色则返回对应的类型名，否则返回'Unknown'
    """
    footnote_array: np.ndarray = full_array[-2:, -2:]  # 右下2x2
    first_pixel: np.ndarray = footnote_array[0, 0]
    if np.all(footnote_array == first_pixel):
        color_string: str = f'{first_pixel[0]},{first_pixel[1]},{first_pixel[2]}'
        return _ColorMap['IconType'].get(color_string, 'Unknown')
    return 'Unknown'


@dataclass
class TitleRecord:
    """标题记录数据类。"""
    id: int
    full_data: bytes  # base64编码的8x8x3数组
    middle_hash: str
    title: str
    match_type: str  # 'manual' | 'cosine'
    created_at: str
    footnote_title: str  # 右下2x2像素区域解析的类型

    @property
    def full_blob(self) -> bytes:
        """兼容属性：返回解码后的full数组字节。"""
        return base64.b64decode(self.full_data)

    @property
    def middle_blob(self) -> bytes:
        """兼容属性：返回middle区域字节。

        从full_data计算而来：full[1:7, 1:7]
        """
        full_array: np.ndarray = np.frombuffer(self.full_blob, dtype=np.uint8).reshape(8, 8, 3)
        middle_array: np.ndarray = full_array[1:7, 1:7]
        return middle_array.tobytes()

    @property
    def footnote_color(self) -> tuple[int, int, int] | None:
        """获取footnote区域的颜色 (右下2x2像素)。

        Returns:
            tuple[int, int, int] | None: 如果footnote是纯色则返回颜色，否则返回None
        """
        full_array: np.ndarray = np.frombuffer(self.full_blob, dtype=np.uint8).reshape(8, 8, 3)
        footnote_array: np.ndarray = full_array[-2:, -2:]  # 右下2x2
        # 检查是否为纯色
        first_pixel: np.ndarray = footnote_array[0, 0]
        if np.all(footnote_array == first_pixel):
            return tuple(first_pixel)
        return None


####### 工具函数 #######

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """计算两个ndarray的余弦相似度。

    Args:
        a: 第一个数组 (6,6,3)
        b: 第二个数组 (6,6,3)

    Returns:
        float: 余弦相似度 (-1 到 1)
    """
    a_flat: np.ndarray = a.flatten().astype(np.float32)
    b_flat: np.ndarray = b.flatten().astype(np.float32)

    norm_a: np.floating = np.linalg.norm(a_flat)
    norm_b: np.floating = np.linalg.norm(b_flat)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a_flat, b_flat) / (norm_a * norm_b))


####### 标题管理器类 #######

class NodeTitleManager:
    """节点标题管理器。

    负责：
    1. 管理SQLite数据库，存储full数据（middle和hash从中计算）
    2. 提供hash快速查找
    3. 提供余弦相似度模糊匹配
    4. 管理未匹配节点（内存中）
    """

    def __init__(self, db_path: str | None = None, similarity_threshold: float = 0.995) -> None:
        """初始化管理器。

        Args:
            db_path: 数据库文件路径，默认使用 app_dir / 'node_titles.db'
            similarity_threshold: 余弦相似度阈值
        """
        if db_path is None:
            db_path = str(app_dir / 'node_titles.db')
        self.db_path: str = db_path
        self.similarity_threshold: float = similarity_threshold

        # 内存中的hash映射表: hash -> (title, id)
        self._hash_map: dict[str, tuple[str, int]] = {}

        # 内存中的所有middle数据: [(id, middle_array, title), ...]
        self._middle_cache: list[tuple[int, np.ndarray, str]] = []

        # 未匹配的hash集合（避免重复计算）
        self._unmatched_hashes: set[str] = set()

        # 未匹配节点列表（用于GUI显示）
        self._unmatched_nodes: list[dict[str, Any]] = []

        # 相似度匹配记录（用于GUI显示）
        self._cosine_matches: list[dict[str, Any]] = []

        # 初始化数据库
        self._init_database()

        # 加载数据到内存
        self._load_data_to_memory()

    def _init_database(self) -> None:
        """初始化数据库表结构。"""
        conn: sqlite3.Connection = sqlite3.connect(self.db_path)
        cursor: sqlite3.Cursor = conn.cursor()

        # 检查是否存在旧表结构
        cursor.execute('PRAGMA table_info(node_titles)')
        columns: set[str] = {col[1] for col in cursor.fetchall()}

        # 如果表不存在，创建新表（包含footnote_title列）
        if not columns:
            cursor.execute('''
                CREATE TABLE node_titles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_data BLOB NOT NULL,
                    middle_hash TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    match_type TEXT DEFAULT 'manual',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    footnote_title TEXT DEFAULT 'Unknown'
                )
            ''')
            print('[NodeTitleManager] 创建新表结构（包含footnote_title列）')
        # 如果存在旧表结构（包含blob列），需要迁移
        elif 'full_blob' in columns or 'middle_blob' in columns:
            print('[NodeTitleManager] 检测到旧表结构，正在迁移数据...')
            self._migrate_from_old_schema(conn, cursor)
        # 如果表存在但没有footnote_title列，添加该列
        elif 'footnote_title' not in columns:
            print('[NodeTitleManager] 检测到旧表结构（缺少footnote_title列），添加新列...')
            cursor.execute('ALTER TABLE node_titles ADD COLUMN footnote_title TEXT DEFAULT "Unknown"')
            print('[NodeTitleManager] 已添加footnote_title列')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hash ON node_titles(middle_hash)
        ''')

        conn.commit()
        conn.close()

    def _migrate_from_old_schema(self, conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
        """从旧表结构迁移数据到新结构。

        旧结构：full_blob, middle_blob
        新结构：full_data (base64编码), footnote_title
        """
        # 重命名旧表
        cursor.execute('ALTER TABLE node_titles RENAME TO node_titles_old')

        # 创建新表（包含footnote_title列）
        cursor.execute('''
            CREATE TABLE node_titles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_data BLOB NOT NULL,
                middle_hash TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                match_type TEXT DEFAULT 'manual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                footnote_title TEXT DEFAULT 'Unknown'
            )
        ''')

        # 迁移数据
        cursor.execute('''
            SELECT id, full_blob, middle_hash, title, match_type, created_at
            FROM node_titles_old
        ''')

        for row in cursor.fetchall():
            id_, full_blob, middle_hash, title, match_type, created_at = row
            # 将full_blob编码为base64
            full_data: bytes = base64.b64encode(full_blob)
            # 计算footnote_title
            full_array: np.ndarray = np.frombuffer(full_blob, dtype=np.uint8).reshape(8, 8, 3)
            footnote_title: str = calculate_footnote_title(full_array)
            cursor.execute('''
                INSERT INTO node_titles (id, full_data, middle_hash, title, match_type, created_at, footnote_title)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (id_, full_data, middle_hash, title, match_type, created_at, footnote_title))

        # 删除旧表
        cursor.execute('DROP TABLE node_titles_old')
        print('[NodeTitleManager] 数据迁移完成（包含footnote_title）')

        conn.commit()

    def _load_data_to_memory(self) -> None:
        """将所有数据加载到内存缓存。"""
        conn: sqlite3.Connection = sqlite3.connect(self.db_path)
        cursor: sqlite3.Cursor = conn.cursor()

        # 加载hash映射
        cursor.execute('SELECT id, middle_hash, title FROM node_titles')
        for row in cursor.fetchall():
            id_, hash_, title = row
            self._hash_map[hash_] = (title, id_)

        # 加载middle数据用于相似度计算（从full_data计算）
        cursor.execute('SELECT id, full_data, title FROM node_titles')
        for row in cursor.fetchall():
            id_, full_data, title = row
            # 解码并计算middle
            full_array: np.ndarray = np.frombuffer(base64.b64decode(full_data), dtype=np.uint8).reshape(8, 8, 3)
            middle_array: np.ndarray = full_array[1:7, 1:7]
            self._middle_cache.append((id_, middle_array, title))

        conn.close()

        print(f'[NodeTitleManager] 已加载 {len(self._hash_map)} 条记录到内存')

    def get_title(
        self,
        middle_hash: str,
        middle_array: np.ndarray,
        full_array: np.ndarray
    ) -> str:
        """获取节点的标题。

        匹配优先级：
        1. hash直接匹配
        2. 余弦相似度匹配
        3. 返回hash并记录为未匹配

        Args:
            middle_hash: 节点middle区域的hash值
            middle_array: 节点middle区域的numpy数组 (6,6,3)
            full_array: 节点full区域的numpy数组 (8,8,3)

        Returns:
            str: 标题或hash
        """
        # 1. 检查hash映射表（O(1)）
        if middle_hash in self._hash_map:
            return self._hash_map[middle_hash][0]

        # 检查是否已在未匹配集合中
        if middle_hash in self._unmatched_hashes:
            return middle_hash

        # 2. 余弦相似度匹配
        best_match: tuple[int, str, np.ndarray] | None = None
        best_similarity: float = -1.0

        for id_, cached_middle, title in self._middle_cache:
            similarity: float = cosine_similarity(middle_array, cached_middle)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = (id_, title, cached_middle)

        # 如果相似度超过阈值，记录并返回
        if best_match and best_similarity >= self.similarity_threshold:
            matched_id, matched_title, matched_middle = best_match

            # 以'cosine'类型添加到数据库
            self.add_title(
                full_array=full_array,
                middle_hash=middle_hash,
                middle_array=middle_array,
                title=matched_title,
                match_type='cosine'
            )

            # 记录到相似度匹配列表
            self._cosine_matches.append({
                'hash': middle_hash,
                'title': matched_title,
                'similarity': best_similarity,
                'full_array': full_array,
                'timestamp': datetime.now().isoformat()
            })

            print(f'[NodeTitleManager] 余弦匹配成功: {matched_title} (相似度: {best_similarity:.4f})')
            return matched_title

        # 3. 未匹配，记录到临时列表
        self._unmatched_hashes.add(middle_hash)

        # 找到最接近的（用于GUI显示）
        closest_title: str = ''
        closest_similarity: float = 0.0
        if best_match:
            closest_title = best_match[1]
            closest_similarity = best_similarity

        self._unmatched_nodes.append({
            'hash': middle_hash,
            'full_array': full_array,
            'middle_array': middle_array,
            'closest_title': closest_title,
            'closest_similarity': closest_similarity,
            'timestamp': datetime.now().isoformat()
        })

        print(f'[NodeTitleManager] 未匹配: {middle_hash} (最接近: {closest_title}, 相似度: {closest_similarity:.4f})')
        return middle_hash

    def add_title(
        self,
        full_array: np.ndarray,
        middle_hash: str,
        middle_array: np.ndarray,
        title: str,
        match_type: str = 'manual'
    ) -> int:
        """添加新的标题记录。

        Args:
            full_array: 节点full区域的numpy数组 (8,8,3)
            middle_hash: middle区域的hash值
            middle_array: middle区域的numpy数组 (6,6,3)
            title: 标题名称
            match_type: 匹配类型 ('manual' 或 'cosine')

        Returns:
            int: 新记录的ID
        """
        # 将full数组编码为base64存储
        full_data: bytes = base64.b64encode(full_array.astype(np.uint8).tobytes())
        # 计算footnote_title
        footnote_title: str = calculate_footnote_title(full_array)

        conn: sqlite3.Connection = sqlite3.connect(self.db_path)
        cursor: sqlite3.Cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO node_titles 
                (full_data, middle_hash, title, match_type, footnote_title)
                VALUES (?, ?, ?, ?, ?)
            ''', (full_data, middle_hash, title, match_type, footnote_title))

            conn.commit()
            new_id: int = cursor.lastrowid if cursor.lastrowid else 0
            if cursor.lastrowid is None:
                # 获取已存在记录的ID
                cursor.execute('SELECT id FROM node_titles WHERE middle_hash = ?', (middle_hash,))
                row: tuple[int] | None = cursor.fetchone()
                new_id = row[0] if row else 0

            # 更新内存缓存
            self._hash_map[middle_hash] = (title, new_id)

            # 检查是否已存在相同的id
            existing_idx: int | None = None
            for i, (id_, _, _) in enumerate(self._middle_cache):
                if id_ == new_id:
                    existing_idx = i
                    break

            if existing_idx is not None:
                self._middle_cache[existing_idx] = (new_id, middle_array, title)
            else:
                self._middle_cache.append((new_id, middle_array, title))

            # 从未匹配集合中移除（如果存在）
            if middle_hash in self._unmatched_hashes:
                self._unmatched_hashes.discard(middle_hash)
                self._unmatched_nodes = [
                    n for n in self._unmatched_nodes
                    if n['hash'] != middle_hash
                ]

            print(f'[NodeTitleManager] 添加记录: {title} (type: {match_type}, footnote: {footnote_title})')
            return new_id

        except sqlite3.Error as e:
            print(f'[NodeTitleManager] 数据库错误: {e}')
            raise
        finally:
            conn.close()

    def delete_title(self, record_id: int) -> bool:
        """删除标题记录。

        Args:
            record_id: 记录ID

        Returns:
            bool: 是否成功
        """
        conn: sqlite3.Connection = sqlite3.connect(self.db_path)
        cursor: sqlite3.Cursor = conn.cursor()

        try:
            # 先获取hash
            cursor.execute('SELECT middle_hash FROM node_titles WHERE id = ?', (record_id,))
            row: tuple[str] | None = cursor.fetchone()

            if not row:
                return False

            hash_to_remove: str = row[0]

            # 删除记录
            cursor.execute('DELETE FROM node_titles WHERE id = ?', (record_id,))
            conn.commit()

            # 更新内存缓存
            if hash_to_remove in self._hash_map:
                del self._hash_map[hash_to_remove]

            self._middle_cache = [
                (id_, arr, title)
                for id_, arr, title in self._middle_cache
                if id_ != record_id
            ]

            print(f'[NodeTitleManager] 删除记录 ID: {record_id}')
            return True

        except sqlite3.Error as e:
            print(f'[NodeTitleManager] 数据库错误: {e}')
            return False
        finally:
            conn.close()

    def update_title(self, record_id: int, new_title: str, match_type: str | None = None) -> bool:
        """更新标题名称。

        Args:
            record_id: 记录ID
            new_title: 新标题
            match_type: 匹配类型（可选，'manual' 或 'cosine'）

        Returns:
            bool: 是否成功
        """
        conn: sqlite3.Connection = sqlite3.connect(self.db_path)
        cursor: sqlite3.Cursor = conn.cursor()

        try:
            if match_type:
                cursor.execute(
                    'UPDATE node_titles SET title = ?, match_type = ? WHERE id = ?',
                    (new_title, match_type, record_id)
                )
            else:
                cursor.execute('UPDATE node_titles SET title = ? WHERE id = ?', (new_title, record_id))
            conn.commit()

            if cursor.rowcount > 0:
                # 更新内存缓存
                for i, (id_, arr, _) in enumerate(self._middle_cache):
                    if id_ == record_id:
                        self._middle_cache[i] = (id_, arr, new_title)
                        break

                # 更新hash映射
                for hash_, (title, id_) in self._hash_map.items():
                    if id_ == record_id:
                        self._hash_map[hash_] = (new_title, id_)
                        break

                print(f'[NodeTitleManager] 更新记录 ID: {record_id} -> {new_title}')
                return True
            return False

        except sqlite3.Error as e:
            print(f'[NodeTitleManager] 数据库错误: {e}')
            return False
        finally:
            conn.close()

    def get_all_titles(self) -> list[TitleRecord]:
        """获取所有标题记录。

        Returns:
            list[TitleRecord]: 记录列表
        """
        conn: sqlite3.Connection = sqlite3.connect(self.db_path)
        cursor: sqlite3.Cursor = conn.cursor()

        cursor.execute('''
            SELECT id, full_data, middle_hash, title, match_type, created_at, footnote_title
            FROM node_titles
            ORDER BY id DESC
        ''')

        records: list[TitleRecord] = []
        for row in cursor.fetchall():
            records.append(TitleRecord(*row))

        conn.close()
        return records

    def get_cosine_matched_records(self) -> list[TitleRecord]:
        """获取所有通过余弦相似度匹配的记录。

        Returns:
            list[TitleRecord]: 记录列表
        """
        conn: sqlite3.Connection = sqlite3.connect(self.db_path)
        cursor: sqlite3.Cursor = conn.cursor()

        cursor.execute('''
            SELECT id, full_data, middle_hash, title, match_type, created_at, footnote_title
            FROM node_titles
            WHERE match_type = 'cosine'
            ORDER BY id DESC
        ''')

        records: list[TitleRecord] = []
        for row in cursor.fetchall():
            records.append(TitleRecord(*row))

        conn.close()
        return records

    def get_stats(self) -> dict[str, int]:
        """获取统计信息。

        Returns:
            dict[str, int]: 统计字典
        """
        conn: sqlite3.Connection = sqlite3.connect(self.db_path)
        cursor: sqlite3.Cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM node_titles')
        total: int = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM node_titles WHERE match_type = 'manual'")
        manual: int = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM node_titles WHERE match_type = 'cosine'")
        cosine: int = cursor.fetchone()[0]

        conn.close()

        return {
            'total': total,
            'manual': manual,
            'cosine': cosine,
            'hash_cached': len(self._hash_map),
            'unmatched_memory': len(self._unmatched_hashes),
            'cosine_matches_session': len(self._cosine_matches)
        }

    def update_threshold(self, new_threshold: float) -> None:
        """更新相似度阈值。

        Args:
            new_threshold: 新阈值 (0.980-0.999)
        """
        self.similarity_threshold = max(0.980, min(0.999, new_threshold))
        print(f'[NodeTitleManager] 阈值更新为: {self.similarity_threshold}')

    def get_unmatched_nodes(self) -> list[dict[str, Any]]:
        """获取当前未匹配的节点列表。

        Returns:
            list[dict[str, Any]]: 未匹配节点信息
        """
        return self._unmatched_nodes.copy()

    def get_cosine_matches(self) -> list[dict[str, Any]]:
        """获取当前会话的相似度匹配记录。

        Returns:
            list[dict[str, Any]]: 匹配记录
        """
        return self._cosine_matches.copy()

    def export_to_json(self, path: str) -> bool:
        """导出数据库到JSON文件。

        Args:
            path: 导出路径

        Returns:
            bool: 是否成功
        """
        try:
            records: list[TitleRecord] = self.get_all_titles()

            export_data: list[dict[str, Any]] = []
            for record in records:
                # 将base64数据转换为list便于JSON序列化
                full_list: list[list[list[int]]] = np.frombuffer(
                    base64.b64decode(record.full_data), dtype=np.uint8
                ).reshape(8, 8, 3).tolist()
                middle_list: list[list[list[int]]] = np.frombuffer(
                    record.middle_blob, dtype=np.uint8
                ).reshape(6, 6, 3).tolist()

                export_data.append({
                    'id': record.id,
                    'full': full_list,
                    'middle': middle_list,
                    'middle_hash': record.middle_hash,
                    'title': record.title,
                    'match_type': record.match_type,
                    'created_at': record.created_at
                })

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            print(f'[NodeTitleManager] 导出 {len(export_data)} 条记录到 {path}')
            return True

        except Exception as e:
            print(f'[NodeTitleManager] 导出失败: {e}')
            return False

    def import_from_json(self, path: str, merge: bool = True) -> bool:
        """从JSON文件导入数据。

        Args:
            path: JSON文件路径
            merge: 是否合并（True）还是覆盖（False）

        Returns:
            bool: 是否成功
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                import_data: list[dict[str, Any]] = json.load(f)

            if not merge:
                # 清空现有数据
                conn: sqlite3.Connection = sqlite3.connect(self.db_path)
                cursor: sqlite3.Cursor = conn.cursor()
                cursor.execute('DELETE FROM node_titles')
                conn.commit()
                conn.close()

                self._hash_map.clear()
                self._middle_cache.clear()

            imported_count: int = 0
            for item in import_data:
                # 创建临时node对象用于add_title
                full_array: np.ndarray = np.array(item['full'], dtype=np.uint8)

                # 检查是否已存在
                if item['middle_hash'] in self._hash_map:
                    continue

                # 直接使用_add_title_with_data方法添加
                self._add_title_with_data(
                    full_array=full_array,
                    middle_hash=item['middle_hash'],
                    title=item['title'],
                    match_type=item.get('match_type', 'manual')
                )
                imported_count += 1

            print(f'[NodeTitleManager] 从 {path} 导入 {imported_count} 条记录')
            return True

        except Exception as e:
            print(f'[NodeTitleManager] 导入失败: {e}')
            return False

    def clear_unmatched_cache(self) -> None:
        """清空未匹配缓存。"""
        self._unmatched_hashes.clear()
        self._unmatched_nodes.clear()
        print('[NodeTitleManager] 已清空未匹配缓存')

    def clear_cosine_matches_cache(self) -> None:
        """清空相似度匹配缓存。"""
        self._cosine_matches.clear()
        print('[NodeTitleManager] 已清空相似度匹配缓存')

    def _add_title_with_data(
        self,
        full_array: np.ndarray,
        middle_hash: str,
        title: str,
        match_type: str = 'manual'
    ) -> int:
        """使用数组数据直接添加标题记录（用于导入）。

        Args:
            full_array: 8x8x3 numpy数组
            middle_hash: 哈希值
            title: 标题名称
            match_type: 匹配类型

        Returns:
            int: 新记录的ID
        """
        # 将full数组编码为base64存储
        full_data: bytes = base64.b64encode(full_array.astype(np.uint8).tobytes())
        middle_array: np.ndarray = full_array[1:7, 1:7]
        # 计算footnote_title
        footnote_title: str = calculate_footnote_title(full_array)

        conn: sqlite3.Connection = sqlite3.connect(self.db_path)
        cursor: sqlite3.Cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO node_titles 
                (full_data, middle_hash, title, match_type, footnote_title)
                VALUES (?, ?, ?, ?, ?)
            ''', (full_data, middle_hash, title, match_type, footnote_title))

            conn.commit()
            new_id: int = cursor.lastrowid if cursor.lastrowid else 0
            if cursor.lastrowid is None:
                # 获取已存在记录的ID
                cursor.execute('SELECT id FROM node_titles WHERE middle_hash = ?', (middle_hash,))
                row: tuple[int] | None = cursor.fetchone()
                new_id = row[0] if row else 0

            # 更新内存缓存
            self._hash_map[middle_hash] = (title, new_id)

            # 检查是否已存在相同的id
            existing_idx: int | None = None
            for i, (id_, _, _) in enumerate(self._middle_cache):
                if id_ == new_id:
                    existing_idx = i
                    break

            if existing_idx is not None:
                self._middle_cache[existing_idx] = (new_id, middle_array, title)
            else:
                self._middle_cache.append((new_id, middle_array, title))

            print(f'[NodeTitleManager] 添加记录: {title} (type: {match_type}, footnote: {footnote_title})')
            return new_id

        except sqlite3.Error as e:
            print(f'[NodeTitleManager] 数据库错误: {e}')
            raise
        finally:
            conn.close()

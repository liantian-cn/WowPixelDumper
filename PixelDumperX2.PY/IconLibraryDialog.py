"""图标库管理对话框 - 9个Tab：6个图标库分类、未匹配图标、相似度匹配记录、设置。

图标库分类:
- 敌人释放的减益 (PLAYER_DEBUFF, BLEED, ENRAGE, POISON, DISEASE, CURSE, MAGIC)
- 玩家施放的减益 (ENEMY_DEBUFF)
- 友方施放的增益 (PLAYER_BUFF)
- 友方施放的技能 (PLAYER_SPELL)
- 敌方释放的技能 (ENEMY_SPELL_INTERRUPTIBLE, ENEMY_SPELL_NOT_INTERRUPTIBLE)
- 其他 (NONE, Unknown)
"""

from typing import Any, cast

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QFileDialog, QGroupBox, QHBoxLayout,
    QHeaderView, QInputDialog, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSlider, QStyledItemDelegate, QStyleOptionViewItem,
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget
)

from Database import NodeTitleManager, TitleRecord
from Node import Node


####### 节点图片委托 #######

class NodeImageDelegate(QStyledItemDelegate):
    """节点图片委托 - 将numpy数组转换为QPixmap并在表格单元格中显示。"""

    def __init__(self, parent: QWidget | None = None, scale: int = 4) -> None:
        """初始化委托。

        Args:
            parent: 父对象
            scale: 缩放倍数（默认4倍，即32x32显示）
        """
        super().__init__(parent)
        self.scale: int = scale

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: Any) -> None:
        """绘制单元格。"""
        # 先绘制背景（选中状态、交替颜色等）
        super().paint(painter, option, index)

        # 从模型数据获取numpy数组
        data = index.data(Qt.ItemDataRole.UserRole)
        if data is None:
            return

        # 转换为QPixmap并绘制
        pixmap: QPixmap | None = self._array_to_pixmap(data)
        if pixmap:
            # 保存 painter 状态
            painter.save()

            # 居中绘制
            rect = cast(Any, option).rect
            x: int = rect.x() + (rect.width() - pixmap.width()) // 2
            y: int = rect.y() + (rect.height() - pixmap.height()) // 2
            painter.drawPixmap(x, y, pixmap)

            # 恢复 painter 状态
            painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: Any) -> Any:
        """返回单元格建议大小。"""
        data = index.data(Qt.ItemDataRole.UserRole)
        if data is not None:
            height, width = data.shape[:2]
            from PySide6.QtCore import QSize
            return QSize(width * self.scale + 8, height * self.scale + 8)
        return super().sizeHint(option, index)

    def _array_to_pixmap(self, arr: np.ndarray) -> QPixmap | None:
        """将numpy数组转换为QPixmap。

        Args:
            arr: numpy数组 (H, W, 3) uint8

        Returns:
            QPixmap: 缩放后的图片
        """
        try:
            if not isinstance(arr, np.ndarray):
                return None

            height: int
            width: int
            height, width = arr.shape[:2]

            # 确保数组形状正确
            image: QImage
            if len(arr.shape) == 3 and arr.shape[2] == 3:
                # RGB格式
                bytes_per_line: int = 3 * width
                image = QImage(
                    arr.data.tobytes(),
                    width,
                    height,
                    bytes_per_line,
                    QImage.Format.Format_RGB888
                )
            elif len(arr.shape) == 2:
                # 灰度格式
                image = QImage(
                    arr.data.tobytes(),
                    width,
                    height,
                    width,
                    QImage.Format.Format_Grayscale8
                )
            else:
                return None

            # 缩放
            scaled: QImage = image.scaled(
                width * self.scale,
                height * self.scale,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.NearestNeighbor
            )

            return QPixmap.fromImage(scaled)

        except Exception:
            return None


####### Hash显示委托 #######

class HashDisplayDelegate(QStyledItemDelegate):
    """Hash显示委托 - 显示shortened hash（前8位...后8位）。"""

    def displayText(self, value: Any, locale: Any) -> str:
        """格式化显示文本。"""
        if isinstance(value, str) and len(value) > 20:
            return f'{value[:8]}...{value[-8:]}'
        return super().displayText(value, locale)


####### 相似度显示委托 #######

class SimilarityDisplayDelegate(QStyledItemDelegate):
    """相似度显示委托 - 显示百分比格式，并根据数值着色。"""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: Any) -> None:
        """绘制带颜色的相似度。"""
        value = index.data()
        if isinstance(value, (int, float)):
            # 根据相似度设置颜色
            color: QColor
            if value >= 0.95:
                color = QColor(0, 150, 0)  # 绿色：高相似度
            elif value >= 0.90:
                color = QColor(200, 150, 0)  # 橙色：中等
            else:
                color = QColor(200, 0, 0)  # 红色：低相似度

            # 绘制背景
            option.palette.setColor(option.palette.ColorRole.Text, color)

        super().paint(painter, option, index)

    def displayText(self, value: Any, locale: Any) -> str:
        """格式化为百分比。"""
        if isinstance(value, (int, float)):
            return f'{value * 100:.2f}%'
        return super().displayText(value, locale)


####### 图标库管理对话框 #######

class IconLibraryDialog(QDialog):
    """图标库管理对话框。"""

    def __init__(self, title_manager: NodeTitleManager, parent: QWidget | None = None) -> None:
        """初始化对话框。

        Args:
            title_manager: NodeTitleManager实例
            parent: 父窗口
        """
        super().__init__(parent)

        self.title_manager: NodeTitleManager = title_manager
        self.setWindowTitle('图标库管理')
        self.resize(1200, 800)

        # 用于跟踪未匹配列表状态，避免不必要的刷新
        self._last_unmatched_count: int = 0
        self._last_unmatched_hashes: set[str] = set()

        # 创建UI
        self.init_ui()

        # 定时刷新未匹配列表（智能刷新，避免焦点丢失）
        self.refresh_timer: QTimer = QTimer(self)
        self.refresh_timer.timeout.connect(self._smart_refresh_unmatched)
        self.refresh_timer.start(1000)  # 每秒检查

        # 初始加载数据
        self.refresh_database_tab()
        self.refresh_unmatched_tab()
        self.refresh_cosine_tab()

    def init_ui(self) -> None:
        """初始化UI。"""
        layout: QVBoxLayout = QVBoxLayout()

        # 创建TabWidget
        self.tab_widget: QTabWidget = QTabWidget()

        # 图标库管理分类Tab定义
        self.icon_categories: list[dict[str, Any]] = [
            {
                'name': '敌人释放的减益',
                'footnotes': ['PLAYER_DEBUFF', 'BLEED', 'ENRAGE', 'POISON', 'DISEASE', 'CURSE', 'MAGIC']
            },
            {
                'name': '玩家施放的减益',
                'footnotes': ['ENEMY_DEBUFF']
            },
            {
                'name': '友方施放的增益',
                'footnotes': ['PLAYER_BUFF']
            },
            {
                'name': '友方施放的技能',
                'footnotes': ['PLAYER_SPELL']
            },
            {
                'name': '敌方释放的技能',
                'footnotes': ['ENEMY_SPELL_INTERRUPTIBLE', 'ENEMY_SPELL_NOT_INTERRUPTIBLE']
            },
            {
                'name': '其他',
                'footnotes': ['NONE', 'Unknown']
            }
        ]

        # Tab 1-6: 图标库管理分类
        self.db_tables: list[QTableWidget] = []
        for category in self.icon_categories:
            tab_widget, table = self._create_database_tab(category)
            self.tab_widget.addTab(tab_widget, category['name'])
            self.db_tables.append(table)

        # Tab 7: 未匹配图标
        self.tab_unmatched: QWidget = self._create_unmatched_tab()
        self.tab_widget.addTab(self.tab_unmatched, '未匹配图标')

        # Tab 8: 相似度匹配记录
        self.tab_cosine: QWidget = self._create_cosine_tab()
        self.tab_widget.addTab(self.tab_cosine, '相似度匹配记录')

        # Tab 9: 设置
        self.tab_settings: QWidget = self._create_settings_tab()
        self.tab_widget.addTab(self.tab_settings, '设置')

        layout.addWidget(self.tab_widget)

        # 底部统计信息
        self.stats_label: QLabel = QLabel('加载中...')
        self.update_stats()
        layout.addWidget(self.stats_label)

        self.setLayout(layout)

    def _create_icon_from_data(self, full_array: np.ndarray, hash_value: str = '') -> QIcon:
        """从数据创建QIcon。

        Args:
            full_array: 8x8x3 numpy数组
            hash_value: hash值（可选，仅用于兼容性）

        Returns:
            QIcon: 创建的图标
        """
        try:
            if isinstance(full_array, np.ndarray):
                height, width = full_array.shape[:2]

                if len(full_array.shape) == 3 and full_array.shape[2] == 3:
                    # RGB格式
                    bytes_per_line: int = 3 * width
                    image: QImage = QImage(
                        full_array.data.tobytes(),
                        width,
                        height,
                        bytes_per_line,
                        QImage.Format.Format_RGB888
                    )
                elif len(full_array.shape) == 2:
                    # 灰度格式
                    image: QImage = QImage(
                        full_array.data.tobytes(),
                        width,
                        height,
                        width,
                        QImage.Format.Format_Grayscale8
                    )
                else:
                    return QIcon()

                # 缩放到32x32
                scaled_image: QImage = image.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio)
                pixmap: QPixmap = QPixmap.fromImage(scaled_image)
                return QIcon(pixmap)

            return QIcon()

        except Exception as e:
            print(f'[_create_icon_from_data] 错误: {e}')
            return QIcon()

    ####### 图标库管理 Tab 1-6 #######

    def _create_database_tab(self, category: dict[str, Any]) -> tuple[QWidget, QTableWidget]:
        """创建图标库管理分类Tab。

        Args:
            category: 分类配置字典，包含 'name' 和 'footnotes'

        Returns:
            tuple: (widget, table) 返回控件和表格引用
        """
        widget: QWidget = QWidget()
        layout: QVBoxLayout = QVBoxLayout()

        # 说明标签
        category_footnotes: str = ', '.join(category['footnotes'])
        info_label: QLabel = QLabel(f"分类: {category['name']}\n包含Footnote类型: {category_footnotes}")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 表格
        db_table: QTableWidget = QTableWidget()
        db_table.setColumnCount(6)
        db_table.setHorizontalHeaderLabels(['图标', '标题', 'Hash', 'Footnote', '类型', '操作'])
        db_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        db_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        db_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        db_table.setColumnWidth(0, 50)
        db_table.setColumnWidth(5, 150)
        db_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        db_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # 设置委托
        db_table.setItemDelegateForColumn(2, HashDisplayDelegate(db_table))

        layout.addWidget(db_table)

        # 操作按钮
        refresh_btn: QPushButton = QPushButton('刷新列表')
        refresh_btn.clicked.connect(self.refresh_database_tab)

        if category['name'] == '其他':
            action_layout: QHBoxLayout = QHBoxLayout()
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(8)

            delete_unknown_btn: QPushButton = QPushButton('删除Unknow分类图标')
            delete_unknown_btn.setStyleSheet('background-color: #f7c9c9;')
            delete_unknown_btn.clicked.connect(self.on_delete_unknown_titles)

            action_layout.addWidget(refresh_btn, 1)
            action_layout.addWidget(delete_unknown_btn, 1)
            layout.addLayout(action_layout)
        else:
            layout.addWidget(refresh_btn)

        widget.setLayout(layout)
        return widget, db_table

    def refresh_database_tab(self) -> None:
        """刷新所有图标库表格。"""
        all_records: list[TitleRecord] = self.title_manager.get_all_titles()

        for i, category in enumerate(self.icon_categories):
            # 筛选符合条件的记录
            filtered_records: list[TitleRecord] = [
                r for r in all_records
                if r.footnote_title in category['footnotes']
            ]
            self._populate_db_table(self.db_tables[i], filtered_records)

        self.update_stats()

    def _populate_db_table(self, table: QTableWidget, records: list[TitleRecord]) -> None:
        """填充数据库表格。

        Args:
            table: 要填充的表格控件
            records: 要显示的记录列表
        """
        table.setRowCount(len(records))

        for row, record in enumerate(records):
            # 设置行高
            table.setRowHeight(row, 40)

            # 图标列 - 使用QIcon直接设置图标
            full_array: np.ndarray = np.frombuffer(record.full_blob, dtype=np.uint8).reshape(8, 8, 3)
            icon: QIcon = self._create_icon_from_data(full_array)

            icon_item: QTableWidgetItem = QTableWidgetItem()
            icon_item.setIcon(icon)
            icon_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row, 0, icon_item)

            # 标题列
            title_item: QTableWidgetItem = QTableWidgetItem(record.title)
            title_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row, 1, title_item)

            # Hash列
            hash_item: QTableWidgetItem = QTableWidgetItem()
            hash_item.setData(Qt.ItemDataRole.DisplayRole, record.middle_hash)
            hash_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row, 2, hash_item)

            # Footnote列
            footnote_item: QTableWidgetItem = QTableWidgetItem(record.footnote_title)
            footnote_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row, 3, footnote_item)

            # 类型列
            type_text: str = '手动添加' if record.match_type == 'manual' else '相似度匹配'
            type_item: QTableWidgetItem = QTableWidgetItem(type_text)
            type_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row, 4, type_item)

            # 操作列 - 编辑和删除按钮
            operation_widget: QWidget = QWidget()
            op_layout: QHBoxLayout = QHBoxLayout()
            op_layout.setContentsMargins(2, 2, 2, 2)

            edit_btn: QPushButton = QPushButton('编辑')
            edit_btn.setProperty('record_id', record.id)
            edit_btn.setProperty('current_title', record.title)
            edit_btn.clicked.connect(self.on_edit_title)

            delete_btn: QPushButton = QPushButton('删除')
            delete_btn.setProperty('record_id', record.id)
            delete_btn.clicked.connect(self.on_delete_title)

            op_layout.addWidget(edit_btn)
            op_layout.addWidget(delete_btn)
            operation_widget.setLayout(op_layout)

            table.setCellWidget(row, 5, operation_widget)

    def _get_category_for_footnote(self, footnote: str) -> dict[str, Any] | None:
        """根据footnote找到对应的分类。

        Args:
            footnote: footnote标题

        Returns:
            分类字典或None
        """
        for category in self.icon_categories:
            if footnote in category['footnotes']:
                return category
        return None

    def on_edit_title(self) -> None:
        """编辑标题。"""
        sender = self.sender()
        if not isinstance(sender, QPushButton):
            return

        record_id: int = sender.property('record_id')
        current_title: str = sender.property('current_title')

        new_title: str
        ok: bool
        new_title, ok = QInputDialog.getText(
            self, '编辑标题', '请输入新标题:', text=current_title
        )

        if ok and new_title and new_title != current_title:
            if self.title_manager.update_title(record_id, new_title, match_type='manual'):
                QMessageBox.information(self, '成功', '标题已更新，类型已设为手动添加')
                self.refresh_database_tab()
            else:
                QMessageBox.warning(self, '失败', '更新失败')

    def on_delete_title(self) -> None:
        """删除标题。"""
        sender = self.sender()
        if not isinstance(sender, QPushButton):
            return

        record_id: int = sender.property('record_id')

        reply: QMessageBox.StandardButton = QMessageBox.question(
            self, '确认删除', '确定要删除这条记录吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.title_manager.delete_title(record_id):
                QMessageBox.information(self, '成功', '记录已删除')
                self.refresh_database_tab()
            else:
                QMessageBox.warning(self, '失败', '删除失败')

    def on_delete_unknown_titles(self) -> None:
        """批量删除Unknown分类标题。"""
        all_records: list[TitleRecord] = self.title_manager.get_all_titles()
        unknown_ids: list[int] = [record.id for record in all_records if record.footnote_title == 'Unknown']

        if not unknown_ids:
            QMessageBox.information(self, '提示', '没有可删除的Unknown分类记录')
            return

        reply: QMessageBox.StandardButton = QMessageBox.question(
            self,
            '确认删除',
            f'确定要删除 {len(unknown_ids)} 条Unknown分类记录吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        success_count: int = 0
        for record_id in unknown_ids:
            if self.title_manager.delete_title(record_id):
                success_count += 1

        self.refresh_database_tab()

        if success_count == len(unknown_ids):
            QMessageBox.information(self, '成功', f'已删除 {success_count} 条Unknown分类记录')
        else:
            QMessageBox.warning(
                self,
                '部分失败',
                f'尝试删除 {len(unknown_ids)} 条，成功 {success_count} 条，失败 {len(unknown_ids) - success_count} 条'
            )

    ####### Tab 2: 未匹配图标 #######

    def _create_unmatched_tab(self) -> QWidget:
        """创建未匹配图标Tab。"""
        widget: QWidget = QWidget()
        layout: QVBoxLayout = QVBoxLayout()

        # 说明标签
        info_label: QLabel = QLabel(
            '以下是在获取标题过程中未能匹配的图标。输入标题后点击"添加"按钮将其加入数据库。\\n'
            '最接近的标题仅供参考。'
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 表格
        self.unmatched_table: QTableWidget = QTableWidget()
        self.unmatched_table.setColumnCount(7)
        self.unmatched_table.setHorizontalHeaderLabels(
            ['图标', 'Hash', '最接近的标题', '相似度', 'Footnote', '输入标题', '操作']
        )
        self.unmatched_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.unmatched_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.unmatched_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.unmatched_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.unmatched_table.setColumnWidth(0, 50)
        self.unmatched_table.setColumnWidth(1, 120)
        self.unmatched_table.setColumnWidth(6, 100)
        self.unmatched_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # 设置委托
        self.unmatched_table.setItemDelegateForColumn(1, HashDisplayDelegate(self.unmatched_table))
        self.unmatched_table.setItemDelegateForColumn(3, SimilarityDisplayDelegate(self.unmatched_table))

        layout.addWidget(self.unmatched_table)

        # 清空按钮
        clear_btn: QPushButton = QPushButton('清空缓存')
        clear_btn.clicked.connect(self.on_clear_unmatched)
        layout.addWidget(clear_btn)

        widget.setLayout(layout)
        return widget

    def refresh_unmatched_tab(self) -> None:
        """刷新未匹配表格。"""
        nodes: list[dict[str, Any]] = self.title_manager.get_unmatched_nodes()

        # 保存当前输入框的内容（输入框现在在第5列）
        current_inputs: dict[str, str] = {}
        for row in range(self.unmatched_table.rowCount()):
            hash_item = self.unmatched_table.item(row, 1)
            if hash_item:
                hash_value: str | None = hash_item.data(Qt.ItemDataRole.UserRole + 1)
                if hash_value:
                    input_widget: QWidget | None = self.unmatched_table.cellWidget(row, 5)
                    if input_widget and isinstance(input_widget, QLineEdit):
                        current_inputs[hash_value] = input_widget.text()

        self.unmatched_table.setRowCount(len(nodes))

        for row, node_info in enumerate(nodes):
            node_array: np.ndarray = node_info['full_array']
            node_hash: str = node_info['hash']

            # 设置行高
            self.unmatched_table.setRowHeight(row, 40)

            # 图标列 - 使用QIcon直接设置图标
            icon: QIcon = self._create_icon_from_data(node_array)
            icon_item: QTableWidgetItem = QTableWidgetItem()
            icon_item.setIcon(icon)
            icon_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.unmatched_table.setItem(row, 0, icon_item)

            # Hash列 - 显示哈希值
            hash_item: QTableWidgetItem = QTableWidgetItem()
            hash_item.setData(Qt.ItemDataRole.DisplayRole, node_hash)
            hash_item.setData(Qt.ItemDataRole.UserRole + 1, node_hash)
            hash_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.unmatched_table.setItem(row, 1, hash_item)

            # 最接近的标题
            closest: str = node_info.get('closest_title', '')
            closest_item: QTableWidgetItem = QTableWidgetItem(closest if closest else '无')
            closest_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.unmatched_table.setItem(row, 2, closest_item)

            # 相似度
            similarity: float = node_info.get('closest_similarity', 0.0)
            sim_item: QTableWidgetItem = QTableWidgetItem()
            sim_item.setData(Qt.ItemDataRole.DisplayRole, similarity)
            sim_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.unmatched_table.setItem(row, 3, sim_item)

            # Footnote列 - 计算右下2x2像素区域的类型
            footnote_array: np.ndarray = node_array[-2:, -2:]  # 右下2x2
            first_pixel: np.ndarray = footnote_array[0, 0]
            if np.all(footnote_array == first_pixel):
                from Utils import _ColorMap
                color_string: str = f'{first_pixel[0]},{first_pixel[1]},{first_pixel[2]}'
                footnote_title: str = _ColorMap['IconType'].get(color_string, 'Unknown')
            else:
                footnote_title = 'Unknown'
            footnote_item: QTableWidgetItem = QTableWidgetItem(footnote_title)
            footnote_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.unmatched_table.setItem(row, 4, footnote_item)

            # 输入标题
            title_input: QLineEdit = QLineEdit()
            if node_hash in current_inputs:
                title_input.setText(current_inputs[node_hash])
            self.unmatched_table.setCellWidget(row, 5, title_input)

            # 添加按钮
            add_btn: QPushButton = QPushButton('添加')
            add_btn.clicked.connect(lambda checked, h=node_hash: self.on_add_unmatched_by_hash(h))
            self.unmatched_table.setCellWidget(row, 6, add_btn)

    def on_add_unmatched_by_hash(self, hash_value: str) -> None:
        """通过hash添加未匹配的节点到数据库。"""
        # 找到对应的node和输入框
        nodes: list[dict[str, Any]] = self.title_manager.get_unmatched_nodes()
        target_node_info: dict[str, Any] | None = None
        target_row: int = -1

        for row, node_info in enumerate(nodes):
            if node_info['hash'] == hash_value:
                target_node_info = node_info
                target_row = row
                break

        if not target_node_info:
            QMessageBox.warning(self, '错误', '找不到对应的节点')
            return

        # 获取输入的标题（输入框现在在第5列）
        title_input: QWidget | None = self.unmatched_table.cellWidget(target_row, 5)
        if not title_input or not isinstance(title_input, QLineEdit):
            return

        title: str = title_input.text().strip()
        if not title:
            QMessageBox.warning(self, '错误', '请输入标题')
            return

        # 添加到数据库
        self.title_manager.add_title(
            full_array=target_node_info['full_array'],
            middle_hash=hash_value,
            middle_array=target_node_info['middle_array'],
            title=title,
            match_type='manual'
        )
        QMessageBox.information(self, '成功', f'已添加: {title}')

        # 刷新两个表格
        self.refresh_unmatched_tab()
        self.refresh_database_tab()

    def on_clear_unmatched(self) -> None:
        """清空未匹配缓存。"""
        self.title_manager.clear_unmatched_cache()
        self.refresh_unmatched_tab()

    def _smart_refresh_unmatched(self) -> None:
        """智能刷新未匹配列表 - 仅在数据变化时刷新，避免焦点丢失。

        当用户在输入框中输入时，如果数据没有变化，则不会重新创建表格，
        从而保持输入框的焦点。
        """
        nodes: list[dict[str, Any]] = self.title_manager.get_unmatched_nodes()

        # 获取当前哈希集合
        current_hashes: set[str] = {node_info['hash'] for node_info in nodes}
        current_count: int = len(nodes)

        # 检查是否有变化
        has_changed: bool = (
            current_count != self._last_unmatched_count or
            current_hashes != self._last_unmatched_hashes
        )

        if has_changed:
            # 保存当前状态
            self._last_unmatched_count = current_count
            self._last_unmatched_hashes = current_hashes

            # 检查是否有输入框处于焦点状态（输入框在第5列）
            has_focus: bool = False
            focused_hash: str | None = None
            focused_text: str = ''

            for row in range(self.unmatched_table.rowCount()):
                input_widget: QWidget | None = self.unmatched_table.cellWidget(row, 5)
                if input_widget and isinstance(input_widget, QLineEdit):
                    if input_widget.hasFocus():
                        has_focus = True
                        hash_item: QTableWidgetItem | None = self.unmatched_table.item(row, 1)
                        if hash_item:
                            focused_hash = hash_item.data(Qt.ItemDataRole.UserRole + 1)
                            focused_text = input_widget.text()
                        break

            # 刷新表格
            self.refresh_unmatched_tab()

            # 如果之前有焦点，尝试恢复
            if has_focus and focused_hash:
                # 查找新的行位置
                for row in range(self.unmatched_table.rowCount()):
                    hash_item: QTableWidgetItem | None = self.unmatched_table.item(row, 1)
                    if hash_item:
                        row_hash: str | None = hash_item.data(Qt.ItemDataRole.UserRole + 1)
                        if row_hash == focused_hash:
                            new_input: QWidget | None = self.unmatched_table.cellWidget(row, 5)
                            if new_input and isinstance(new_input, QLineEdit):
                                new_input.setText(focused_text)
                                new_input.setFocus()
                            break

    ####### Tab 3: 相似度匹配记录 #######

    def _create_cosine_tab(self) -> QWidget:
        """创建相似度匹配记录Tab。"""
        widget: QWidget = QWidget()
        layout: QVBoxLayout = QVBoxLayout()

        # 说明标签
        info_label: QLabel = QLabel(
            '以下是通过余弦相似度算法在本会话中自动匹配的图标。\\n'
            "这些图标已自动添加到数据库（类型为'相似度匹配'）。"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 表格
        self.cosine_table: QTableWidget = QTableWidget()
        self.cosine_table.setColumnCount(5)
        self.cosine_table.setHorizontalHeaderLabels(
            ['图标', '匹配到的标题', '相似度', '时间', '操作']
        )
        self.cosine_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cosine_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.cosine_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.cosine_table.setColumnWidth(0, 50)
        self.cosine_table.setColumnWidth(4, 100)
        self.cosine_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # 设置委托
        self.cosine_table.setItemDelegateForColumn(2, SimilarityDisplayDelegate(self.cosine_table))

        layout.addWidget(self.cosine_table)

        # 清空按钮
        clear_btn: QPushButton = QPushButton('清空会话记录')
        clear_btn.clicked.connect(self.on_clear_cosine)
        layout.addWidget(clear_btn)

        widget.setLayout(layout)
        return widget

    def refresh_cosine_tab(self) -> None:
        """刷新相似度匹配表格。"""
        matches: list[dict[str, Any]] = self.title_manager.get_cosine_matches()
        self.cosine_table.setRowCount(len(matches))

        for row, match_info in enumerate(matches):
            node_array: np.ndarray = match_info['full_array']

            # 设置行高
            self.cosine_table.setRowHeight(row, 40)

            # 图标列 - 使用QIcon直接设置图标
            icon: QIcon = self._create_icon_from_data(node_array)
            icon_item: QTableWidgetItem = QTableWidgetItem()
            icon_item.setIcon(icon)
            icon_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.cosine_table.setItem(row, 0, icon_item)

            # 匹配到的标题
            title_item: QTableWidgetItem = QTableWidgetItem(match_info['title'])
            title_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.cosine_table.setItem(row, 1, title_item)

            # 相似度
            similarity: float = match_info.get('similarity', 0.0)
            sim_item: QTableWidgetItem = QTableWidgetItem()
            sim_item.setData(Qt.ItemDataRole.DisplayRole, float(similarity))
            sim_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.cosine_table.setItem(row, 2, sim_item)

            # 时间
            time_item: QTableWidgetItem = QTableWidgetItem(match_info.get('timestamp', ''))
            time_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.cosine_table.setItem(row, 3, time_item)

            # 操作 - 查看详情或删除
            detail_btn: QPushButton = QPushButton('查看')
            detail_btn.clicked.connect(lambda checked, m=match_info: self.show_cosine_detail(m))
            self.cosine_table.setCellWidget(row, 4, detail_btn)

    def show_cosine_detail(self, match_info: dict[str, Any]) -> None:
        """显示相似度匹配详情。"""
        msg: str = (
            f"Hash: {match_info['hash']}\\n"
            f"匹配标题: {match_info['title']}\\n"
            f"相似度: {match_info['similarity']:.4f} ({match_info['similarity']*100:.2f}%)\\n"
            f"时间: {match_info.get('timestamp', 'N/A')}"
        )

        QMessageBox.information(self, '匹配详情', msg)

    def on_clear_cosine(self) -> None:
        """清空相似度匹配缓存。"""
        self.title_manager.clear_cosine_matches_cache()
        self.refresh_cosine_tab()

    ####### Tab 9: 设置 #######

    def _create_settings_tab(self) -> QWidget:
        """创建设置Tab。"""
        widget: QWidget = QWidget()
        layout: QVBoxLayout = QVBoxLayout()

        # 相似度阈值设置
        threshold_group: QGroupBox = QGroupBox('余弦相似度阈值')
        threshold_layout: QVBoxLayout = QVBoxLayout()

        # 滑块
        slider_layout: QHBoxLayout = QHBoxLayout()
        self.threshold_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(980, 999)
        self.threshold_slider.setValue(int(round(self.title_manager.similarity_threshold * 1000)))
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        slider_layout.addWidget(self.threshold_slider)

        # 数值显示
        self.threshold_label: QLabel = QLabel(f'{self.title_manager.similarity_threshold:.3f}')
        self.threshold_label.setFixedWidth(60)
        slider_layout.addWidget(self.threshold_label)

        threshold_layout.addLayout(slider_layout)

        # 说明
        info_text: QLabel = QLabel(
            '阈值说明:\n'
            '- 0.995 (推荐): 非常严格的匹配，只匹配高度相似的图标\n'
            '- 0.980: 更宽松的匹配，可能匹配到相似但不完全相同的图标\n'
            '- 低于0.980: 容易误匹配，不推荐'
        )
        info_text.setWordWrap(True)
        threshold_layout.addWidget(info_text)

        threshold_group.setLayout(threshold_layout)
        layout.addWidget(threshold_group)

        # 数据库信息
        db_group: QGroupBox = QGroupBox('数据库信息')
        db_layout: QVBoxLayout = QVBoxLayout()

        self.db_info_label: QLabel = QLabel('加载中...')
        self.update_db_info()
        db_layout.addWidget(self.db_info_label)

        db_group.setLayout(db_layout)
        layout.addWidget(db_group)

        # 数据导入导出
        import_export_group: QGroupBox = QGroupBox('数据导入导出')
        import_export_layout: QHBoxLayout = QHBoxLayout()

        self.export_btn: QPushButton = QPushButton('导出JSON')
        self.export_btn.clicked.connect(self.on_export)
        import_export_layout.addWidget(self.export_btn)

        self.import_btn: QPushButton = QPushButton('导入JSON')
        self.import_btn.clicked.connect(self.on_import)
        import_export_layout.addWidget(self.import_btn)

        import_export_group.setLayout(import_export_layout)
        layout.addWidget(import_export_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def on_export(self) -> None:
        """导出到JSON。"""
        path: str
        _filter: str
        path, _filter = QFileDialog.getSaveFileName(
            self, '导出图标库', 'node_titles.json', 'JSON文件 (*.json)'
        )
        if path:
            if self.title_manager.export_to_json(path):
                QMessageBox.information(self, '成功', f'已导出到:\\n{path}')
            else:
                QMessageBox.warning(self, '失败', '导出失败')

    def on_import(self) -> None:
        """从JSON导入。"""
        path: str
        _filter: str
        path, _filter = QFileDialog.getOpenFileName(
            self, '导入图标库', '', 'JSON文件 (*.json)'
        )
        if path:
            reply: QMessageBox.StandardButton = QMessageBox.question(
                self, '导入方式', '选择导入方式:\\nYes = 合并现有数据\\nNo = 覆盖现有数据\\nCancel = 取消',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Cancel:
                return

            merge: bool = (reply == QMessageBox.StandardButton.Yes)

            if self.title_manager.import_from_json(path, merge=merge):
                QMessageBox.information(self, '成功', '导入完成')
                self.refresh_database_tab()
            else:
                QMessageBox.warning(self, '失败', '导入失败')

    def on_threshold_changed(self, value: int) -> None:
        """阈值滑块变化。"""
        threshold: float = value / 1000.0
        self.title_manager.update_threshold(threshold)
        self.threshold_label.setText(f'{threshold:.3f}')

    def update_db_info(self) -> None:
        """更新数据库信息。"""
        stats: dict[str, int] = self.title_manager.get_stats()
        info: str = (
            f"数据库路径: {self.title_manager.db_path}\n"
            f"总记录数: {stats['total']}\n"
            f"手动添加: {stats['manual']}\n"
            f"相似度匹配: {stats['cosine']}\n"
            f"Hash缓存: {stats['hash_cached']}\n"
            f"当前未匹配(内存): {stats['unmatched_memory']}\n"
            f"会话相似度匹配: {stats['cosine_matches_session']}"
        )
        self.db_info_label.setText(info)

    def update_stats(self) -> None:
        """更新统计信息。"""
        stats: dict[str, int] = self.title_manager.get_stats()
        text: str = (
            f"总记录: {stats['total']} | "
            f"手动添加: {stats['manual']} | "
            f"相似度匹配: {stats['cosine']} | "
            f"当前未匹配: {stats['unmatched_memory']}"
        )
        self.stats_label.setText(text)

    def closeEvent(self, event: Any) -> None:
        """关闭事件。"""
        self.refresh_timer.stop()
        super().closeEvent(event)

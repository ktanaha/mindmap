"""
マインドマップビューウィジェット

右ペインのマインドマップ表示エリア
"""
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsLineItem
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter
from typing import Optional, Dict, Tuple
from src.domain.node import Node


class MindMapView(QGraphicsView):
    """マインドマップを表示するビュー"""

    def __init__(self, parent=None) -> None:
        """
        ビューを初期化する

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self._setup_ui()

        # ノードの表示位置を管理
        self._node_positions: Dict[str, tuple] = {}

    def _setup_ui(self) -> None:
        """UIをセットアップする"""
        # 背景色
        self.setBackgroundBrush(QBrush(QColor(250, 250, 250)))

        # アンチエイリアス
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ドラッグモード
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def display_tree(self, root: Optional[Node]) -> None:
        """
        ノードツリーを表示する

        Args:
            root: ルートノード
        """
        # シーンをクリア
        self._scene.clear()
        self._node_positions.clear()

        if root is None:
            return

        # 左から右にツリーを描画（ルートノードは左側に配置）
        start_x = 100
        start_y = 300
        self._draw_node_horizontal(root, start_x, start_y, 0)

        # シーンのサイズを調整
        self._scene.setSceneRect(self._scene.itemsBoundingRect())

    def _calculate_subtree_height(self, node: Node) -> float:
        """
        サブツリー全体の高さを計算する

        Args:
            node: ノード

        Returns:
            サブツリーの高さ
        """
        if not node.children:
            return 50  # 単一ノードの高さ（テキスト1行分）

        total_height = 0
        for child in node.children:
            total_height += self._calculate_subtree_height(child)

        return max(total_height, 50)

    def _draw_node_horizontal(self, node: Node, x: float, y: float, depth: int) -> float:
        """
        ノードとその子孫を横方向に再帰的に描画する

        Args:
            node: 描画するノード
            x: X座標（ノードの左端）
            y: Y座標（このノードの中心）
            depth: 階層の深さ

        Returns:
            このサブツリーが占める高さ
        """
        # ノードのテキストを描画
        text_item = QGraphicsTextItem(node.text)
        text_font = QFont("Arial", 13, QFont.Weight.Normal)
        text_item.setFont(text_font)

        # 深さに応じてテキスト色を変える
        colors = [
            QColor(30, 60, 150),    # 濃い青
            QColor(50, 90, 180),    # 青
            QColor(70, 110, 200),   # 薄青
            QColor(90, 130, 220),   # 更に薄青
        ]
        color_index = min(depth, len(colors) - 1)
        text_item.setDefaultTextColor(colors[color_index])

        # テキストの位置を設定（Y座標はテキストの中心がyになるように）
        text_rect = text_item.boundingRect()
        text_y = y - text_rect.height() / 2
        text_item.setPos(x, text_y)
        self._scene.addItem(text_item)

        # 下線を描画
        underline_y = text_y + text_rect.height() + 2
        underline = QGraphicsLineItem(x, underline_y,
                                      x + text_rect.width(), underline_y)
        underline_pen = QPen(colors[color_index], 2)
        underline.setPen(underline_pen)
        self._scene.addItem(underline)

        # ノードの境界を記録（接続線用）
        node_right = x + text_rect.width()
        node_center_y = y

        # 位置を記録
        self._node_positions[node.id] = (x, y)

        # 子ノードを描画
        if not node.children:
            return 50  # 単一ノードの高さ

        # 子ノードの配置
        horizontal_spacing = 80  # 横方向の間隔（親から子への距離）
        vertical_spacing = 40    # 縦方向の間隔（兄弟ノード間）- 重ならないように増加

        # 全ての子ノードのサブツリー高さを計算
        child_heights = [self._calculate_subtree_height(child) for child in node.children]
        total_height = sum(child_heights) + vertical_spacing * (len(node.children) - 1)

        # 子ノードの開始Y座標（中央揃え）
        current_y = y - total_height / 2

        for i, child in enumerate(node.children):
            child_x = node_right + horizontal_spacing
            child_center_y = current_y + child_heights[i] / 2

            # 親から子への線を描画
            line_pen = QPen(QColor(150, 150, 150), 1.5)
            # 親ノードの右端から子ノードの左端へ
            self._scene.addLine(node_right + 5, node_center_y,
                              child_x - 5, child_center_y,
                              line_pen)

            # 子ノードを再帰的に描画
            self._draw_node_horizontal(child, child_x, child_center_y, depth + 1)

            # 次の子ノードのY座標
            current_y += child_heights[i] + vertical_spacing

        return total_height

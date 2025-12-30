"""
マインドマップビューウィジェット

右ペインのマインドマップ表示エリア
"""
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsPathItem
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPainterPath
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
        text_font = QFont("Arial", 16, QFont.Weight.Normal)
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
        horizontal_spacing = 120  # 横方向の間隔（親から子への距離）- 右に広がるように増加
        vertical_spacing = 40     # 縦方向の間隔（兄弟ノード間）- 重ならないように増加

        # 全ての子ノードのサブツリー高さを計算
        child_heights = [self._calculate_subtree_height(child) for child in node.children]
        total_height = sum(child_heights) + vertical_spacing * (len(node.children) - 1)

        # 子ノードの開始Y座標（中央揃え）
        current_y = y - total_height / 2

        for i, child in enumerate(node.children):
            child_x = node_right + horizontal_spacing
            child_center_y = current_y + child_heights[i] / 2

            # 親から子への曲線を描画（ベジェ曲線）
            path = QPainterPath()
            start_x = node_right + 5
            start_y = node_center_y
            end_x = child_x - 5
            end_y = child_center_y

            # ベジェ曲線の制御点を計算（右方向になめらかに曲がるように）
            # 横方向の距離の半分を制御点の位置として使用
            control_offset = (end_x - start_x) * 0.5

            # 開始点
            path.moveTo(start_x, start_y)

            # 3次ベジェ曲線（cubicTo）で滑らかな曲線を描画
            # 第1制御点: 親ノードから右方向に伸びる
            # 第2制御点: 子ノードから左方向に伸びる
            path.cubicTo(
                start_x + control_offset, start_y,  # 第1制御点
                end_x - control_offset, end_y,      # 第2制御点
                end_x, end_y                        # 終点
            )

            # パスを描画
            path_item = QGraphicsPathItem(path)
            path_pen = QPen(QColor(150, 150, 150), 2)
            path_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            path_item.setPen(path_pen)
            self._scene.addItem(path_item)

            # 子ノードを再帰的に描画
            self._draw_node_horizontal(child, child_x, child_center_y, depth + 1)

            # 次の子ノードのY座標
            current_y += child_heights[i] + vertical_spacing

        return total_height

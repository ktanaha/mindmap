"""
マインドマップビューウィジェット

右ペインのマインドマップ表示エリア
"""
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPathItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QPainterPath
from typing import Optional, Dict, Tuple, List
from src.domain.node import Node
from src.presentation.node_item import NodeItem


class MindMapView(QGraphicsView):
    """マインドマップを表示するビュー"""

    # ノードが付け替えられたときのシグナル
    node_reparented = pyqtSignal(Node, Node)

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

        # ノードアイテムを管理
        self._node_items: Dict[str, NodeItem] = {}
        self._root_node: Optional[Node] = None

        # ズームレベル管理
        self._zoom_level = 1.0
        self._zoom_min = 0.1
        self._zoom_max = 3.0

        # パン（移動）管理
        self._is_panning = False
        self._pan_start_pos = None

    def _setup_ui(self) -> None:
        """UIをセットアップする"""
        # 背景色
        self.setBackgroundBrush(QBrush(QColor(250, 250, 250)))

        # アンチエイリアス
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ドラッグモードは無効化（ノードのドラッグを優先）
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def display_tree(self, root: Optional[Node]) -> None:
        """
        ノードツリーを表示する

        Args:
            root: ルートノード
        """
        # シーンをクリア
        self._scene.clear()
        self._node_items.clear()
        self._root_node = root

        if root is None:
            return

        # 仮想ルートノードの場合は、子ノードたちを最上位として並べて表示
        if root.text == "__virtual_root__":
            start_x = 100
            start_y = 100
            vertical_spacing = 40

            # 各トップレベルノードの高さを計算
            child_heights = [self._calculate_subtree_height(child) for child in root.children]
            total_height = sum(child_heights) + vertical_spacing * (len(root.children) - 1)

            current_y = start_y
            for i, child in enumerate(root.children):
                child_center_y = current_y + child_heights[i] / 2
                self._draw_node_horizontal(child, start_x, child_center_y, 0)
                current_y += child_heights[i] + vertical_spacing
        else:
            # 通常のルートノードの場合
            start_x = 100
            start_y = 300
            self._draw_node_horizontal(root, start_x, start_y, 0)

        # 接続線を描画
        self._draw_connections()

        # シーンのサイズを調整（余白を追加）
        items_rect = self._scene.itemsBoundingRect()
        margin = 100  # 左右上下の余白
        self._scene.setSceneRect(
            items_rect.x() - margin,
            items_rect.y() - margin,
            items_rect.width() + margin * 2,
            items_rect.height() + margin * 2
        )

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
        # NodeItemを作成
        node_item = NodeItem(node, depth)
        node_item.setPos(x, y - node_item.boundingRect().height() / 2)
        self._scene.addItem(node_item)
        self._node_items[node.id] = node_item

        # ドロップイベントを接続
        node_item.node_dropped.connect(self._on_node_dropped)

        # ノードの右端を計算
        node_right = x + node_item.boundingRect().width()

        # 子ノードを描画
        if not node.children:
            return 50  # 単一ノードの高さ

        # 子ノードの配置
        horizontal_spacing = 120  # 横方向の間隔（親から子への距離）
        vertical_spacing = 40     # 縦方向の間隔（兄弟ノード間）

        # 全ての子ノードのサブツリー高さを計算
        child_heights = [self._calculate_subtree_height(child) for child in node.children]
        total_height = sum(child_heights) + vertical_spacing * (len(node.children) - 1)

        # 子ノードの開始Y座標（中央揃え）
        current_y = y - total_height / 2

        for i, child in enumerate(node.children):
            child_x = node_right + horizontal_spacing
            child_center_y = current_y + child_heights[i] / 2

            # 子ノードを再帰的に描画
            self._draw_node_horizontal(child, child_x, child_center_y, depth + 1)

            # 次の子ノードのY座標
            current_y += child_heights[i] + vertical_spacing

        return total_height

    def _draw_connections(self) -> None:
        """全ノード間の接続線を描画する"""
        for node_id, node_item in self._node_items.items():
            node = node_item.node
            if node.parent is None:
                continue

            # 親ノードのアイテムを取得
            parent_item = self._node_items.get(node.parent.id)
            if parent_item is None:
                continue

            # 親と子の位置を取得
            parent_pos = parent_item.scenePos()
            parent_rect = parent_item.boundingRect()
            child_pos = node_item.scenePos()

            # 親ノードの右端と子ノードの左端を接続
            start_x = parent_pos.x() + parent_rect.width() + 5
            start_y = parent_pos.y() + parent_rect.height() / 2
            end_x = child_pos.x() - 5
            end_y = child_pos.y() + node_item.boundingRect().height() / 2

            # ベジェ曲線で接続
            path = QPainterPath()
            path.moveTo(start_x, start_y)

            control_offset = (end_x - start_x) * 0.5
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
            path_item.setZValue(-1)  # ノードの背面に配置
            self._scene.addItem(path_item)

    def _on_node_dropped(self, dropped_node: Node, target_node: Node) -> None:
        """
        ノードがドロップされたときの処理

        Args:
            dropped_node: ドロップされたノード
            target_node: ドロップ先のノード
        """
        # 親子関係を変更
        if dropped_node.parent is not None:
            dropped_node.parent.remove_child(dropped_node)
        target_node.add_child(dropped_node)

        # ビューを再描画
        self.display_tree(self._root_node)

        # 変更をシグナルで通知
        self.node_reparented.emit(dropped_node, target_node)

    def wheelEvent(self, event) -> None:
        """
        マウスホイールイベントを処理（拡大縮小）

        Args:
            event: ホイールイベント
        """
        # ホイールの回転量を取得
        delta = event.angleDelta().y()

        # ズーム倍率を計算（1ノッチで15%の拡大縮小）
        zoom_factor = 1.15 if delta > 0 else 1 / 1.15

        # 新しいズームレベルを計算
        new_zoom = self._zoom_level * zoom_factor

        # ズームレベルの範囲制限
        if new_zoom < self._zoom_min or new_zoom > self._zoom_max:
            return

        # ズームレベルを更新
        self._zoom_level = new_zoom

        # マウスカーソル位置を中心に拡大縮小
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.scale(zoom_factor, zoom_factor)

        event.accept()

    def mousePressEvent(self, event) -> None:
        """
        マウス押下イベントを処理

        Args:
            event: マウスイベント
        """
        # 中クリックまたは右クリックでパン開始
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.RightButton:
            self._is_panning = True
            self._pan_start_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """
        マウス移動イベントを処理

        Args:
            event: マウスイベント
        """
        if self._is_panning and self._pan_start_pos is not None:
            # パン中：ビューをスクロール
            delta = event.pos() - self._pan_start_pos
            self._pan_start_pos = event.pos()

            # 水平・垂直スクロールバーの値を変更
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """
        マウスリリースイベントを処理

        Args:
            event: マウスイベント
        """
        # パン終了
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.RightButton:
            if self._is_panning:
                self._is_panning = False
                self._pan_start_pos = None
                self.setCursor(Qt.CursorShape.ArrowCursor)
                event.accept()
                return

        super().mouseReleaseEvent(event)

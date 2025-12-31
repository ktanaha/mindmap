"""
ドラッグ可能なノードアイテム

マインドマップのノードを表現するQGraphicsItemで、ドラッグ&ドロップ機能を持つ
"""
from PyQt6.QtWidgets import QGraphicsObject, QGraphicsTextItem, QGraphicsLineItem
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPen, QColor, QFont, QPainter
from typing import Optional
from src.domain.node import Node


class NodeItem(QGraphicsObject):
    """ドラッグ可能なノードアイテム"""

    # ノードがドロップされたときのシグナル (dropped_node, target_node)
    node_dropped = pyqtSignal(Node, Node)

    def __init__(self, node: Node, depth: int, parent=None) -> None:
        """
        ノードアイテムを初期化する

        Args:
            node: ドメインモデルのNode
            depth: 階層の深さ
            parent: 親アイテム
        """
        super().__init__(parent)
        self._node = node
        self._depth = depth
        self._is_dragging = False
        self._drag_start_pos = None
        self._hover_target: Optional['NodeItem'] = None

        # 深さに応じた色設定
        self._colors = [
            QColor(30, 60, 150),    # 濃い青
            QColor(50, 90, 180),    # 青
            QColor(70, 110, 200),   # 薄青
            QColor(90, 130, 220),   # 更に薄青
        ]

        # テキストアイテムを作成
        self._text_item = QGraphicsTextItem(node.text, self)
        text_font = QFont("Arial", 16, QFont.Weight.Normal)
        self._text_item.setFont(text_font)
        color_index = min(depth, len(self._colors) - 1)
        self._text_item.setDefaultTextColor(self._colors[color_index])

        # 下線アイテムを作成
        text_rect = self._text_item.boundingRect()
        underline_y = text_rect.height() + 2
        self._underline = QGraphicsLineItem(0, underline_y,
                                           text_rect.width(), underline_y, self)
        underline_pen = QPen(self._colors[color_index], 2)
        self._underline.setPen(underline_pen)

        # ドラッグ可能に設定
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsMovable, False)  # 自動移動は無効化
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

    @property
    def node(self) -> Node:
        """ドメインモデルのNodeを取得"""
        return self._node

    @property
    def depth(self) -> int:
        """階層の深さを取得"""
        return self._depth

    def boundingRect(self) -> QRectF:
        """アイテムの境界矩形を返す"""
        text_rect = self._text_item.boundingRect()
        return QRectF(0, 0, text_rect.width(), text_rect.height() + 4)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """
        カスタム描画（必要に応じて）

        Note: 子アイテム（text_item, underline）が自動的に描画されるため、
        ここでは選択状態やドラッグ中の視覚効果のみ描画
        """
        if self._is_dragging or self.isSelected():
            # ドラッグ中または選択中はハイライト表示
            rect = self.boundingRect()
            painter.setPen(QPen(QColor(255, 165, 0), 2))  # オレンジ色
            painter.setBrush(QColor(255, 200, 100, 50))   # 半透明オレンジ
            painter.drawRect(rect.adjusted(-5, -5, 5, 5))

    def mousePressEvent(self, event) -> None:
        """マウス押下イベント"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.scenePos()
            self.setOpacity(0.7)  # 半透明化
            self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """マウス移動イベント"""
        if self._is_dragging:
            # ドロップ先候補を検出（ノードは動かさない）
            self._update_hover_target(event.scenePos())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """マウスリリースイベント"""
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False
            self.setOpacity(1.0)  # 不透明に戻す

            # ドロップ先がある場合、シグナルを発火
            if self._hover_target is not None:
                # 先にハイライトを解除（シグナル発火後にアイテムが削除されるため）
                self._hover_target.set_highlight(False)
                target_node = self._hover_target.node
                self._hover_target = None
                # シグナルを発火（この時点でシーンが再構築され、self自身も削除される）
                self.node_dropped.emit(self._node, target_node)
                # シグナル発火後は何もしない（self自身が削除されている）
                return

            self.update()
        super().mouseReleaseEvent(event)

    def _update_hover_target(self, scene_pos) -> None:
        """
        ドロップ先候補を更新

        Args:
            scene_pos: 現在のマウス位置（シーン座標）
        """
        # 前のハイライトをクリア
        if self._hover_target is not None:
            self._hover_target.set_highlight(False)
            self._hover_target = None

        # 現在位置の下にあるアイテムを検索
        items = self.scene().items(scene_pos)
        for item in items:
            if isinstance(item, NodeItem) and item != self:
                # 自分自身の子孫ノードには付け替えできない
                if not self._is_descendant(item.node):
                    self._hover_target = item
                    item.set_highlight(True)
                    break

    def _is_descendant(self, node: Node) -> bool:
        """
        指定されたノードが自分の子孫かどうかを判定

        Args:
            node: 判定するノード

        Returns:
            子孫ノードの場合True
        """
        def check_recursive(current: Node) -> bool:
            if current == node:
                return True
            for child in current.children:
                if check_recursive(child):
                    return True
            return False

        return check_recursive(self._node)

    def set_highlight(self, highlight: bool) -> None:
        """
        ハイライト表示を設定

        Args:
            highlight: True=ハイライト、False=通常
        """
        if highlight:
            self._text_item.setDefaultTextColor(QColor(255, 100, 0))  # オレンジ色
            color_index = min(self._depth, len(self._colors) - 1)
            self._underline.setPen(QPen(QColor(255, 100, 0), 3))  # 太く
        else:
            color_index = min(self._depth, len(self._colors) - 1)
            self._text_item.setDefaultTextColor(self._colors[color_index])
            self._underline.setPen(QPen(self._colors[color_index], 2))
        self.update()

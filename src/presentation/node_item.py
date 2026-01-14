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
    # ノードが選択されたときのシグナル
    node_selected = pyqtSignal(object)  # NodeItemを渡す

    def __init__(self, node: Node, depth: int, font_size: int = 14, font_color: QColor = None, parent=None) -> None:
        """
        ノードアイテムを初期化する

        Args:
            node: ドメインモデルのNode
            depth: 階層の深さ
            font_size: フォントサイズ
            font_color: フォント色
            parent: 親アイテム
        """
        super().__init__(parent)
        self._node = node
        self._depth = depth
        self._is_dragging = False
        self._drag_start_pos = None
        self._drag_start_item_pos = None  # ドラッグ開始時のアイテムの位置
        self._hover_target: Optional['NodeItem'] = None
        self._ghost_text: Optional[QGraphicsTextItem] = None
        self._ghost_underline: Optional[QGraphicsLineItem] = None
        self._is_selected = False  # 選択状態
        self._is_focused = False  # フォーカス状態（カーソル位置に対応）

        # フォント設定（Nodeに設定があればそれを使用、なければデフォルト）
        self._default_font_size = font_size
        self._default_font_color = font_color if font_color is not None else QColor(0, 0, 0)

        # ノード個別の設定があれば優先
        if node.font_size is not None:
            self._font_size = node.font_size
        else:
            self._font_size = self._default_font_size

        if node.font_color is not None:
            self._font_color = QColor(node.font_color)
        else:
            self._font_color = self._default_font_color

        # テキストアイテムを作成
        self._text_item = QGraphicsTextItem(node.text, self)
        text_font = QFont("Arial", self._font_size, QFont.Weight.Normal)
        self._text_item.setFont(text_font)
        self._text_item.setDefaultTextColor(self._font_color)
        # boundingRectが(-15, -15)から始まるので、テキストを(15, 15)にオフセット
        self._text_item.setPos(15, 15)

        # 下線アイテムを作成
        text_rect = self._text_item.boundingRect()
        underline_y = text_rect.height() + 2 + 15  # テキストのオフセット分を追加
        self._underline = QGraphicsLineItem(15, underline_y,
                                           text_rect.width() + 15, underline_y, self)
        underline_pen = QPen(self._font_color, 2)
        self._underline.setPen(underline_pen)

        # ドラッグ可能に設定
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsMovable, True)  # ドラッグで移動可能に
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemSendsGeometryChanges, True)  # 位置変更を検出
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
        # 選択枠とドラッグ&ドロップ用の余白を含める
        # 上下左右に15pxの余白を追加して、ドロップ先として認識される範囲を広げる
        return QRectF(-15, -15, text_rect.width() + 30, text_rect.height() + 34)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """
        カスタム描画（必要に応じて）

        Note: 子アイテム（text_item, underline）が自動的に描画されるため、
        ここでは選択状態やドラッグ中の視覚効果のみ描画
        """
        # テキストを囲む矩形を計算（テキストと下線を含む）
        text_rect = self._text_item.boundingRect()
        # テキストは(15, 15)の位置にあり、下線は text_rect.height() + 2 + 15 の位置にある
        # 適度なパディングを持たせてテキストを中心に配置
        padding = 8
        content_x = 15 - padding
        content_y = 15 - padding
        content_width = text_rect.width() + padding * 2
        # 下線の位置を考慮した高さ（テキストの高さ + 下線までの余白 + パディング）
        content_height = text_rect.height() + 4 + padding * 2
        content_rect = QRectF(content_x, content_y, content_width, content_height)

        # フォーカス状態の背景（一番下に描画）
        if self._is_focused:
            painter.setPen(QPen(QColor(255, 100, 100, 180), 2))  # 薄い赤枠
            painter.setBrush(QColor(220, 220, 220, 120))  # 薄いグレー
            painter.drawRoundedRect(content_rect, 5, 5)

        if self._is_dragging:
            # ドラッグ中は半透明オレンジ
            painter.setPen(QPen(QColor(255, 165, 0), 2))
            painter.setBrush(QColor(255, 200, 100, 50))
            painter.drawRoundedRect(content_rect, 5, 5)
        elif self._is_selected:
            # 選択中は青い枠線と薄い背景
            painter.setPen(QPen(QColor(50, 150, 250), 3))
            painter.setBrush(QColor(180, 220, 255, 80))
            painter.drawRoundedRect(content_rect, 5, 5)

    def mousePressEvent(self, event) -> None:
        """マウス押下イベント"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.scenePos()
            self._drag_start_item_pos = self.pos()  # アイテムの元の位置を保存
            self.setOpacity(0.7)  # 半透明化

            # ゴーストアイテム（カーソルに追従する半透明テキスト）を作成
            self._create_ghost(event.scenePos())

            self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """マウス移動イベント"""
        if self._is_dragging:
            # ゴーストアイテムをカーソル位置に移動
            self._update_ghost(event.scenePos())

            # ドロップ先候補を検出（ノードは動かさない）
            self._update_hover_target(event.scenePos())
            # ドラッグ中はノード本体を動かさない（接続線の残像を防ぐため）
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """マウスリリースイベント"""
        # ドラッグ中であれば、どのボタンでも終了処理を行う
        if self._is_dragging:
            self._is_dragging = False
            self.setOpacity(1.0)  # 不透明に戻す

            # ゴーストアイテムを削除
            self._remove_ghost()

            # 左クリックでドロップ先がある場合のみ、シグナルを発火
            if event.button() == Qt.MouseButton.LeftButton and self._hover_target is not None:
                # 先にハイライトを解除（シグナル発火後にアイテムが削除されるため）
                self._hover_target.set_highlight(False)
                target_node = self._hover_target.node
                self._hover_target = None
                # シグナルを発火（この時点でシーンが再構築され、self自身も削除される）
                self.node_dropped.emit(self._node, target_node)
                # シグナル発火後は何もしない（self自身が削除されている）
                return

            # ドロップしなかった場合はハイライトをクリア
            if self._hover_target is not None:
                self._hover_target.set_highlight(False)
                self._hover_target = None

            # ドロップしなかった場合の処理
            if event.button() == Qt.MouseButton.LeftButton:
                if self._drag_start_pos is not None:
                    current_pos = event.scenePos()
                    drag_distance = (current_pos - self._drag_start_pos).manhattanLength()
                    if drag_distance > 5:  # ドラッグした場合は元の位置に戻す
                        if self._drag_start_item_pos is not None:
                            self.setPos(self._drag_start_item_pos)
                    else:  # ほとんど移動していない場合は選択状態をトグル
                        self.set_selected(not self._is_selected)
                        self.node_selected.emit(self)
                else:
                    # ドラッグ開始位置がない場合は選択状態をトグル
                    self.set_selected(not self._is_selected)
                    self.node_selected.emit(self)

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
            self._underline.setPen(QPen(QColor(255, 100, 0), 3))  # 太く
        else:
            # フォント色を元に戻す
            self._text_item.setDefaultTextColor(self._font_color)
            self._underline.setPen(QPen(self._font_color, 2))
        self.update()

    def set_selected(self, selected: bool) -> None:
        """
        選択状態を設定

        Args:
            selected: True=選択、False=非選択
        """
        self._is_selected = selected
        self.update()

    def is_selected(self) -> bool:
        """
        選択状態を取得

        Returns:
            選択されている場合True
        """
        return self._is_selected

    def set_focused(self, focused: bool) -> None:
        """
        フォーカス状態を設定

        Args:
            focused: True=フォーカス、False=非フォーカス
        """
        self._is_focused = focused
        self.update()

    def _create_ghost(self, scene_pos) -> None:
        """
        ゴーストアイテム（カーソルに追従する半透明テキスト）を作成

        Args:
            scene_pos: 初期位置（シーン座標）
        """
        # ゴーストテキストアイテムを作成
        self._ghost_text = QGraphicsTextItem(self._node.text)
        text_font = QFont("Arial", self._font_size, QFont.Weight.Normal)
        self._ghost_text.setFont(text_font)
        ghost_color = QColor(self._font_color)
        ghost_color.setAlpha(150)  # 半透明
        self._ghost_text.setDefaultTextColor(ghost_color)
        self._ghost_text.setZValue(1000)  # 最前面に表示

        # ゴースト下線アイテムを作成
        text_rect = self._ghost_text.boundingRect()
        underline_y = text_rect.height() + 2
        self._ghost_underline = QGraphicsLineItem(0, underline_y,
                                                  text_rect.width(), underline_y)
        ghost_pen = QPen(ghost_color, 2)
        self._ghost_underline.setPen(ghost_pen)
        self._ghost_underline.setZValue(1000)

        # シーンに追加
        self.scene().addItem(self._ghost_text)
        self.scene().addItem(self._ghost_underline)

        # 初期位置を設定
        self._update_ghost(scene_pos)

    def _update_ghost(self, scene_pos) -> None:
        """
        ゴーストアイテムをカーソル位置に移動

        Args:
            scene_pos: カーソル位置（シーン座標）
        """
        if self._ghost_text is not None and self._ghost_underline is not None:
            # テキストの位置を設定（カーソルの少し右下に表示）
            offset_x = 10
            offset_y = 10
            self._ghost_text.setPos(scene_pos.x() + offset_x, scene_pos.y() + offset_y)

            # 下線の位置を設定
            text_rect = self._ghost_text.boundingRect()
            underline_y = scene_pos.y() + offset_y + text_rect.height() + 2
            self._ghost_underline.setLine(
                scene_pos.x() + offset_x,
                underline_y,
                scene_pos.x() + offset_x + text_rect.width(),
                underline_y
            )

    def _remove_ghost(self) -> None:
        """ゴーストアイテムを削除"""
        if self._ghost_text is not None:
            scene = self.scene()
            if scene is not None:
                scene.removeItem(self._ghost_text)
            self._ghost_text = None

        if self._ghost_underline is not None:
            scene = self.scene()
            if scene is not None:
                scene.removeItem(self._ghost_underline)
            self._ghost_underline = None

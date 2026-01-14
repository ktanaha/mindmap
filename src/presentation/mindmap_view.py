"""
マインドマップビューウィジェット

右ペインのマインドマップ表示エリア
"""
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPathItem
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QEvent
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QPainterPath, QImage
from PyQt6.QtWidgets import QPinchGesture
from typing import Optional, Dict, Tuple, List
from src.domain.node import Node
from src.presentation.node_item import NodeItem


class MindMapView(QGraphicsView):
    """マインドマップを表示するビュー"""

    # ノードが付け替えられたときのシグナル
    node_reparented = pyqtSignal(Node, Node)
    # ノードがクリックされたときのシグナル（ノードを渡す）
    node_clicked = pyqtSignal(Node)
    # テキスト入力をエディタに転送するシグナル（キーイベントのテキストを渡す）
    forward_text_input = pyqtSignal(str)

    def __init__(self, parent=None, font_size: int = 14, font_color: QColor = None, line_color: QColor = None, layout_direction: int = 0) -> None:
        """
        ビューを初期化する

        Args:
            parent: 親ウィジェット
            font_size: フォントサイズ
            font_color: フォント色
            line_color: 線の色
            layout_direction: レイアウト方向（0=右のみ, 1=左右交互, 2=下のみ, 3=上下交互）
        """
        super().__init__(parent)
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self._setup_ui()

        # ノードアイテムを管理
        self._node_items: Dict[str, NodeItem] = {}
        self._root_node: Optional[Node] = None
        self._selected_node_item: Optional[NodeItem] = None  # 選択中のノード
        self._focused_node_item: Optional[NodeItem] = None  # フォーカス中のノード（カーソル位置）

        # フォント設定
        self._font_size = font_size
        self._font_color = font_color if font_color is not None else QColor(0, 0, 0)
        self._line_color = line_color if line_color is not None else QColor(150, 150, 150)
        self._layout_direction = layout_direction  # 0: 右のみ, 1: 左右交互

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

        # トラックパッドのスムーズスクロールを有効化
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # ピンチジェスチャーを有効化
        self.grabGesture(Qt.GestureType.PinchGesture)

    def display_tree(self, root: Optional[Node]) -> None:
        """
        ノードツリーを表示する

        Args:
            root: ルートノード
        """
        # シーンをクリア
        self._scene.clear()
        self._node_items.clear()
        self._selected_node_item = None  # 選択状態もクリア
        self._focused_node_item = None  # フォーカス状態もクリア
        self._root_node = root

        if root is None:
            return

        # 仮想ルートノードの場合は、子ノードたちを最上位として並べて表示
        if root.text == "__virtual_root__":
            if self._layout_direction == 0:
                # 右のみモード：縦に並べる
                start_x = 100
                start_y = 100
                vertical_spacing = 40

                # 各トップレベルノードの高さを計算
                child_heights = [self._calculate_subtree_height(child, vertical_spacing) for child in root.children]
                total_height = sum(child_heights) + vertical_spacing * (len(root.children) - 1)

                current_y = start_y
                for i, child in enumerate(root.children):
                    child_center_y = current_y + child_heights[i] / 2
                    self._draw_node_with_direction(child, start_x, child_center_y, 0, direction=1, vertical_spacing=vertical_spacing)
                    current_y += child_heights[i] + vertical_spacing
            elif self._layout_direction == 1:
                # 左右交互モード：左右に振り分ける（対称的に配置）
                center_x = 500
                vertical_spacing = 80  # 左右で重ならないように間隔を広げる

                # 各トップレベルノードの高さを計算
                child_heights = [self._calculate_subtree_height(child, vertical_spacing) for child in root.children]

                # 左側と右側に分ける（合計高さができるだけ均等になるように）
                left_children = []
                right_children = []
                left_total = 0
                right_total = 0

                # 高さが大きい順にソート
                children_with_heights = [(root.children[i], child_heights[i]) for i in range(len(root.children))]
                children_with_heights.sort(key=lambda x: x[1], reverse=True)

                # 貪欲法で左右に振り分け
                for child, height in children_with_heights:
                    if left_total <= right_total:
                        left_children.append((child, height))
                        left_total += height
                    else:
                        right_children.append((child, height))
                        right_total += height

                # 左右の合計高さを計算（スペース込み）
                left_total_height = sum(h for _, h in left_children) + vertical_spacing * (len(left_children) - 1) if left_children else 0
                right_total_height = sum(h for _, h in right_children) + vertical_spacing * (len(right_children) - 1) if right_children else 0

                # 両側の高さの最大値を取得して、中央揃えにする
                max_height = max(left_total_height, right_total_height)
                center_y = 300

                # 右側を配置（中央揃え）
                start_y_right = center_y - right_total_height / 2
                current_y = start_y_right
                for child, height in right_children:
                    child_center_y = current_y + height / 2
                    self._draw_node_with_direction(child, center_x + 50, child_center_y, 0, direction=1, vertical_spacing=vertical_spacing)
                    current_y += height + vertical_spacing

                # 左側を配置（中央揃え）
                start_y_left = center_y - left_total_height / 2
                current_y = start_y_left
                for child, height in left_children:
                    child_center_y = current_y + height / 2
                    self._draw_node_with_direction(child, center_x - 50, child_center_y, 0, direction=-1, vertical_spacing=vertical_spacing)
                    current_y += height + vertical_spacing
            elif self._layout_direction == 2:
                # 下のみモード：横に並べる
                start_x = 100
                start_y = 100
                horizontal_spacing = 80

                # 各トップレベルノードの幅を計算
                child_widths = [self._calculate_subtree_width(child, horizontal_spacing) for child in root.children]
                total_width = sum(child_widths) + horizontal_spacing * (len(root.children) - 1)

                current_x = start_x
                for i, child in enumerate(root.children):
                    child_center_x = current_x + child_widths[i] / 2
                    self._draw_node_vertical(child, child_center_x, start_y, 0, direction=1, horizontal_spacing=horizontal_spacing)
                    current_x += child_widths[i] + horizontal_spacing
            else:
                # 上下交互モード：上下に振り分ける（対称的に配置）
                center_y = 300
                horizontal_spacing = 120  # 上下で重ならないように間隔を広げる

                # 各トップレベルノードの幅を計算
                child_widths = [self._calculate_subtree_width(child, horizontal_spacing) for child in root.children]

                # 上側と下側に分ける（合計幅ができるだけ均等になるように）
                top_children = []
                bottom_children = []
                top_total = 0
                bottom_total = 0

                # 幅が大きい順にソート
                children_with_widths = [(root.children[i], child_widths[i]) for i in range(len(root.children))]
                children_with_widths.sort(key=lambda x: x[1], reverse=True)

                # 貪欲法で上下に振り分け
                for child, width in children_with_widths:
                    if top_total <= bottom_total:
                        top_children.append((child, width))
                        top_total += width
                    else:
                        bottom_children.append((child, width))
                        bottom_total += width

                # 上下の合計幅を計算（スペース込み）
                top_total_width = sum(w for _, w in top_children) + horizontal_spacing * (len(top_children) - 1) if top_children else 0
                bottom_total_width = sum(w for _, w in bottom_children) + horizontal_spacing * (len(bottom_children) - 1) if bottom_children else 0

                # 中央揃えで配置
                center_x = 500
                start_x_top = center_x - top_total_width / 2
                start_x_bottom = center_x - bottom_total_width / 2

                # 下側を配置
                current_x = start_x_bottom
                for child, width in bottom_children:
                    child_center_x = current_x + width / 2
                    self._draw_node_vertical(child, child_center_x, center_y + 50, 0, direction=1, horizontal_spacing=horizontal_spacing)
                    current_x += width + horizontal_spacing

                # 上側を配置
                current_x = start_x_top
                for child, width in top_children:
                    child_center_x = current_x + width / 2
                    self._draw_node_vertical(child, child_center_x, center_y - 50, 0, direction=-1, horizontal_spacing=horizontal_spacing)
                    current_x += width + horizontal_spacing
        else:
            # 通常のルートノードの場合
            if self._layout_direction == 0:
                # 右のみ
                vertical_spacing = 40
                start_x = 100
                start_y = 300
                self._draw_node_with_direction(root, start_x, start_y, 0, direction=1, vertical_spacing=vertical_spacing)
            elif self._layout_direction == 1:
                # 左右交互：ルートを中央に配置
                vertical_spacing = 40
                start_x = 500
                start_y = 300
                self._draw_node_with_direction(root, start_x, start_y, 0, direction=0, vertical_spacing=vertical_spacing)
            elif self._layout_direction == 2:
                # 下のみ
                horizontal_spacing = 80
                start_x = 400
                start_y = 100
                self._draw_node_vertical(root, start_x, start_y, 0, direction=1, horizontal_spacing=horizontal_spacing)
            else:
                # 上下交互：ルートを中央に配置
                horizontal_spacing = 80
                start_x = 400
                start_y = 300
                self._draw_node_vertical(root, start_x, start_y, 0, direction=0, horizontal_spacing=horizontal_spacing)

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

    def _calculate_subtree_height(self, node: Node, vertical_spacing: float = 40) -> float:
        """
        サブツリー全体の高さを計算する

        Args:
            node: ノード
            vertical_spacing: 兄弟ノード間の垂直間隔

        Returns:
            サブツリーの高さ
        """
        if not node.children:
            return 60  # 単一ノードの高さ（テキスト + マージン）

        # 各子のサブツリー高さを計算
        child_heights = [self._calculate_subtree_height(child, vertical_spacing) for child in node.children]

        # 子ノード間の間隔を含めた合計高さ
        total_height = sum(child_heights) + vertical_spacing * (len(node.children) - 1)

        return max(total_height, 60)

    def _calculate_subtree_width(self, node: Node, horizontal_spacing: float = 80) -> float:
        """
        サブツリー全体の幅を計算する（縦方向レイアウト用）

        Args:
            node: ノード
            horizontal_spacing: 兄弟ノード間の水平間隔

        Returns:
            サブツリーの幅
        """
        if not node.children:
            return 200  # 単一ノードの幅（テキスト幅の概算 + マージン）

        # 各子のサブツリー幅を計算
        child_widths = [self._calculate_subtree_width(child, horizontal_spacing) for child in node.children]

        # 子ノード間の間隔を含めた合計幅
        total_width = sum(child_widths) + horizontal_spacing * (len(node.children) - 1)

        return max(total_width, 200)

    def _draw_node_with_direction(self, node: Node, x: float, y: float, depth: int, direction: int, vertical_spacing: float = 40) -> float:
        """
        ノードとその子孫を指定方向に再帰的に描画する

        Args:
            node: 描画するノード
            x: X座標（direction=1の場合は左端、direction=-1の場合は右端）
            y: Y座標（このノードの中心）
            depth: 階層の深さ
            direction: 描画方向（1=右、-1=左、0=ルート（子を左右に振り分け））
            vertical_spacing: 兄弟ノード間の垂直間隔

        Returns:
            このサブツリーが占める高さ
        """
        # NodeItemを作成
        node_item = NodeItem(node, depth, self._font_size, self._font_color)

        # 手動配置されたノードの場合は保存された位置を使用
        if node.manual_position:
            pos = node.position
            node_x = pos[0]  # 子ノードの配置計算のためにnode_xを設定
            node_item.setPos(pos[0], pos[1])
        else:
            # direction=-1（左）の場合は、xからノード幅を引いた位置に配置
            if direction == -1:
                node_x = x - node_item.boundingRect().width()
            else:
                node_x = x

            node_item.setPos(node_x, y - node_item.boundingRect().height() / 2)

        self._scene.addItem(node_item)
        self._node_items[node.id] = node_item

        # イベントを接続
        node_item.node_dropped.connect(self._on_node_dropped)
        node_item.node_selected.connect(self._on_node_selected)

        # 子ノードを描画
        if not node.children:
            return 50  # 単一ノードの高さ

        # 子ノードの配置
        horizontal_spacing = 120  # 横方向の間隔（親から子への距離）

        # 全ての子ノードのサブツリー高さを計算
        child_heights = [self._calculate_subtree_height(child, vertical_spacing) for child in node.children]
        total_height = sum(child_heights) + vertical_spacing * (len(node.children) - 1)

        # 子ノードの開始Y座標（中央揃え）
        current_y = y - total_height / 2

        for i, child in enumerate(node.children):
            if direction == 0:
                # ルートノード：子を左右交互に配置
                child_direction = 1 if i % 2 == 0 else -1
                if child_direction == 1:
                    child_x = node_x + node_item.boundingRect().width() + horizontal_spacing
                else:
                    child_x = node_x - horizontal_spacing
            elif direction == 1:
                # 右方向：通常通り右に配置
                child_direction = 1
                child_x = node_x + node_item.boundingRect().width() + horizontal_spacing
            else:
                # 左方向：左に配置
                child_direction = -1
                child_x = node_x - horizontal_spacing

            child_center_y = current_y + child_heights[i] / 2

            # 子ノードを再帰的に描画
            self._draw_node_with_direction(child, child_x, child_center_y, depth + 1, child_direction, vertical_spacing)

            # 次の子ノードのY座標
            current_y += child_heights[i] + vertical_spacing

        return total_height

    def _draw_node_vertical(self, node: Node, x: float, y: float, depth: int, direction: int, horizontal_spacing: float = 80) -> float:
        """
        ノードとその子孫を上下方向に再帰的に描画する

        Args:
            node: 描画するノード
            x: X座標（このノードの中心）
            y: Y座標（direction=1の場合は上端、direction=-1の場合は下端）
            depth: 階層の深さ
            direction: 描画方向（1=下、-1=上、0=ルート（子を上下に振り分け））
            horizontal_spacing: 兄弟ノード間の水平間隔

        Returns:
            このサブツリーが占める幅
        """
        # NodeItemを作成
        node_item = NodeItem(node, depth, self._font_size, self._font_color)

        # 手動配置されたノードの場合は保存された位置を使用
        if node.manual_position:
            pos = node.position
            node_x = pos[0]  # 子ノードの配置計算のためにnode_xを設定
            node_y = pos[1]  # 子ノードの配置計算のためにnode_yを設定
            node_item.setPos(pos[0], pos[1])
        else:
            # ノードを配置（x座標を中心に配置）
            node_x = x - node_item.boundingRect().width() / 2

            # direction=-1（上）の場合は、yからノード高さを引いた位置に配置
            if direction == -1:
                node_y = y - node_item.boundingRect().height()
            else:
                node_y = y

            node_item.setPos(node_x, node_y)

        self._scene.addItem(node_item)
        self._node_items[node.id] = node_item

        # イベントを接続
        node_item.node_dropped.connect(self._on_node_dropped)
        node_item.node_selected.connect(self._on_node_selected)

        # 子ノードを描画
        if not node.children:
            return 200  # 単一ノードの幅

        # 子ノードの配置
        vertical_spacing = 80  # 縦方向の間隔（親から子への距離）

        # 全ての子ノードのサブツリー幅を計算
        child_widths = [self._calculate_subtree_width(child, horizontal_spacing) for child in node.children]
        total_width = sum(child_widths) + horizontal_spacing * (len(node.children) - 1)

        # 子ノードの開始X座標（中央揃え）
        current_x = x - total_width / 2

        for i, child in enumerate(node.children):
            if direction == 0:
                # ルートノード：子を上下交互に配置
                child_direction = 1 if i % 2 == 0 else -1
                if child_direction == 1:
                    child_y = node_y + node_item.boundingRect().height() + vertical_spacing
                else:
                    child_y = node_y - vertical_spacing
            elif direction == 1:
                # 下方向：通常通り下に配置
                child_direction = 1
                child_y = node_y + node_item.boundingRect().height() + vertical_spacing
            else:
                # 上方向：上に配置
                child_direction = -1
                child_y = node_y - vertical_spacing

            child_center_x = current_x + child_widths[i] / 2

            # 子ノードを再帰的に描画
            self._draw_node_vertical(child, child_center_x, child_y, depth + 1, child_direction, horizontal_spacing)

            # 次の子ノードのX座標
            current_x += child_widths[i] + horizontal_spacing

        return total_width

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
            child_rect = node_item.boundingRect()

            # 親と子の中心座標を計算
            parent_center_x = parent_pos.x() + parent_rect.width() / 2
            parent_center_y = parent_pos.y() + parent_rect.height() / 2
            child_center_x = child_pos.x() + child_rect.width() / 2
            child_center_y = child_pos.y() + child_rect.height() / 2

            # 常に左右方向（水平方向）の接続を使用
            if child_center_x > parent_center_x:
                # 子が右側：親ノードの右端と子ノードの左端を接続
                start_x = parent_pos.x() + parent_rect.width() + 5
                start_y = parent_pos.y() + parent_rect.height() / 2
                end_x = child_pos.x() - 5
                end_y = child_pos.y() + child_rect.height() / 2
            else:
                # 子が左側：親ノードの左端と子ノードの右端を接続
                start_x = parent_pos.x() - 5
                start_y = parent_pos.y() + parent_rect.height() / 2
                end_x = child_pos.x() + child_rect.width() + 5
                end_y = child_pos.y() + child_rect.height() / 2

            # ベジェ曲線で接続
            path = QPainterPath()
            path.moveTo(start_x, start_y)

            control_offset = abs(end_x - start_x) * 0.5
            if child_center_x > parent_center_x:
                # 右方向
                path.cubicTo(
                    start_x + control_offset, start_y,  # 第1制御点
                    end_x - control_offset, end_y,      # 第2制御点
                    end_x, end_y                        # 終点
                )
            else:
                # 左方向
                path.cubicTo(
                    start_x - control_offset, start_y,  # 第1制御点
                    end_x + control_offset, end_y,      # 第2制御点
                    end_x, end_y                        # 終点
                )

            # パスを描画
            path_item = QGraphicsPathItem(path)
            path_pen = QPen(self._line_color, 2)
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

        # 変更をシグナルで通知（シグナルハンドラ内で中心表示を行う）
        self.node_reparented.emit(dropped_node, target_node)

    def _on_node_selected(self, node_item: NodeItem) -> None:
        """
        ノードが選択されたときの処理

        Args:
            node_item: 選択されたNodeItem
        """
        # 前の選択を解除
        if self._selected_node_item is not None and self._selected_node_item != node_item:
            self._selected_node_item.set_selected(False)

        # 新しい選択を保存
        if node_item.is_selected():
            self._selected_node_item = node_item
            # ノードがクリックされたことを通知
            self.node_clicked.emit(node_item.node)
        else:
            self._selected_node_item = None

    def get_selected_node(self) -> Optional[Node]:
        """
        選択中のノードを取得

        Returns:
            選択中のNode、なければNone
        """
        if self._selected_node_item is not None:
            return self._selected_node_item.node
        return None

    def wheelEvent(self, event) -> None:
        """
        マウスホイール/トラックパッドイベントを処理

        Args:
            event: ホイールイベント
        """
        # ホイールの回転量を取得
        delta_y = event.angleDelta().y()
        delta_x = event.angleDelta().x()

        # Cmd/Ctrlキーが押されている場合、またはピンチジェスチャーの場合はズーム
        if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier):
            if delta_y == 0:
                return

            # ズーム倍率を計算（トラックパッドのスムーズなピンチに対応）
            # delta_yの値を小さくしてスムーズにズーム
            zoom_factor = 1.0 + (delta_y / 1200.0)

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
        else:
            # 通常のスクロール（パン）
            # 2本指スワイプでスムーズにパン
            # 垂直スクロール
            if delta_y != 0:
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - delta_y
                )

            # 水平スクロール
            if delta_x != 0:
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - delta_x
                )

            event.accept()

    def mousePressEvent(self, event) -> None:
        """
        マウス押下イベントを処理

        Args:
            event: マウスイベント
        """
        # 中クリック、右クリック、またはSpaceキー+左クリックでパン開始
        if (event.button() == Qt.MouseButton.MiddleButton or
            event.button() == Qt.MouseButton.RightButton or
            (event.button() == Qt.MouseButton.LeftButton and
             event.modifiers() & Qt.KeyboardModifier.ShiftModifier)):
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
        if (event.button() == Qt.MouseButton.MiddleButton or
            event.button() == Qt.MouseButton.RightButton or
            event.button() == Qt.MouseButton.LeftButton):
            if self._is_panning:
                self._is_panning = False
                self._pan_start_pos = None
                self.setCursor(Qt.CursorShape.ArrowCursor)
                event.accept()
                return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        """
        キー押下イベントを処理

        Args:
            event: キーイベント
        """
        # テキスト入力可能なキーの場合、エディタに転送
        text = event.text()
        if text and text.isprintable() and not event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # 入力可能な文字（Ctrl修飾子がない場合）をエディタに転送
            self.forward_text_input.emit(text)
            event.accept()
            return

        # その他のキーは通常処理
        super().keyPressEvent(event)

    def event(self, event) -> bool:
        """
        イベントを処理（ジェスチャー検出用）

        Args:
            event: イベント

        Returns:
            イベントが処理された場合True
        """
        if event.type() == QEvent.Type.Gesture:
            return self._gesture_event(event)
        return super().event(event)

    def _gesture_event(self, event) -> bool:
        """
        ジェスチャーイベントを処理

        Args:
            event: ジェスチャーイベント

        Returns:
            イベントが処理された場合True
        """
        pinch = event.gesture(Qt.GestureType.PinchGesture)
        if pinch:
            return self._pinch_triggered(pinch)
        return True

    def _pinch_triggered(self, gesture: QPinchGesture) -> bool:
        """
        ピンチジェスチャーを処理

        Args:
            gesture: ピンチジェスチャー

        Returns:
            イベントが処理された場合True
        """
        change_flags = gesture.changeFlags()

        # スケール変更がある場合
        if change_flags & QPinchGesture.ChangeFlag.ScaleFactorChanged:
            # 現在のスケールファクターを取得
            current_scale = gesture.scaleFactor()

            # 新しいズームレベルを計算
            new_zoom = self._zoom_level * current_scale

            # ズームレベルの範囲制限
            if new_zoom < self._zoom_min or new_zoom > self._zoom_max:
                return True

            # ズームレベルを更新
            self._zoom_level = new_zoom

            # ジェスチャーの中心点を取得
            center_point = gesture.centerPoint()

            # ビューポート座標をシーン座標に変換
            scene_pos = self.mapToScene(center_point.toPoint())

            # 中心点を基準にズーム
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
            self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)

            # 現在の中心点のビューポート座標を保存
            old_pos = self.mapFromScene(scene_pos)

            # スケールを適用
            self.scale(current_scale, current_scale)

            # 新しい中心点のビューポート座標を取得
            new_pos = self.mapFromScene(scene_pos)

            # 差分を計算してビューを移動
            delta = new_pos - old_pos
            self.horizontalScrollBar().setValue(
                int(self.horizontalScrollBar().value() + delta.x())
            )
            self.verticalScrollBar().setValue(
                int(self.verticalScrollBar().value() + delta.y())
            )

        return True

    def set_font_size(self, size: int) -> None:
        """
        フォントサイズを設定する

        Args:
            size: フォントサイズ
        """
        self._font_size = size

    def set_font_color(self, color: QColor) -> None:
        """
        フォント色を設定する

        Args:
            color: フォント色
        """
        self._font_color = color

    def set_line_color(self, color: QColor) -> None:
        """
        線の色を設定する

        Args:
            color: 線の色
        """
        self._line_color = color

    def set_layout_direction(self, direction: int) -> None:
        """
        レイアウト方向を設定する

        Args:
            direction: 0=右のみ、1=左右交互、2=下のみ、3=上下交互
        """
        self._layout_direction = direction

    def center_on_node(self, node: Node) -> None:
        """
        指定されたノードを中心に表示し、フォーカス状態にする

        Args:
            node: 中心に表示するノード
        """
        # ノードに対応するNodeItemを検索
        node_item = self._node_items.get(node.id)
        if node_item is None:
            return

        # 前のフォーカスを解除
        if self._focused_node_item is not None and self._focused_node_item != node_item:
            self._focused_node_item.set_focused(False)

        # 新しいノードにフォーカスを設定
        node_item.set_focused(True)
        self._focused_node_item = node_item

        # ノードの中心座標を計算
        node_pos = node_item.scenePos()
        node_rect = node_item.boundingRect()
        center_x = node_pos.x() + node_rect.width() / 2
        center_y = node_pos.y() + node_rect.height() / 2

        # ビューの中心をノードの中心に移動
        self.centerOn(center_x, center_y)

    def export_to_png(self, file_path: str) -> bool:
        """
        マインドマップをPNG形式でエクスポートする

        Args:
            file_path: 保存先ファイルパス

        Returns:
            成功したらTrue、失敗したらFalse
        """
        try:
            # シーン内のアイテムの境界矩形を取得
            scene_rect = self._scene.itemsBoundingRect()

            # マージンを追加（見栄えを良くするため）
            margin = 50
            scene_rect.adjust(-margin, -margin, margin, margin)

            # QImageを作成（白背景）
            image = QImage(
                int(scene_rect.width()),
                int(scene_rect.height()),
                QImage.Format.Format_ARGB32
            )
            image.fill(Qt.GlobalColor.white)

            # QPainterでシーンをレンダリング
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            # シーンを描画
            self._scene.render(painter, QRectF(), scene_rect)
            painter.end()

            # PNG形式で保存
            return image.save(file_path, "PNG")
        except Exception as e:
            print(f"PNG エクスポートエラー: {e}")
            return False

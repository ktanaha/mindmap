"""
Nodeドメインモデル

マインドマップの各ノード（節点）を表現するクラス
"""
from typing import Optional, List, Tuple
import uuid


class Node:
    """マインドマップのノード"""

    def __init__(self, text: str, font_size: Optional[int] = None, font_color: Optional[str] = None) -> None:
        """
        ノードを初期化する

        Args:
            text: ノードのテキスト内容
            font_size: フォントサイズ（Noneの場合はデフォルト）
            font_color: フォント色（Noneの場合はデフォルト、カラーコード文字列）
        """
        self._id: str = str(uuid.uuid4())
        self._text: str = text
        self._parent: Optional[Node] = None
        self._children: List[Node] = []
        self._position: Tuple[int, int] = (0, 0)
        self._font_size: Optional[int] = font_size
        self._font_color: Optional[str] = font_color  # カラーコード（例: "#FF0000"）

    @property
    def id(self) -> str:
        """ノードの一意識別子を取得"""
        return self._id

    @property
    def text(self) -> str:
        """ノードのテキストを取得"""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """ノードのテキストを設定"""
        self._text = value

    @property
    def parent(self) -> Optional["Node"]:
        """親ノードを取得"""
        return self._parent

    @property
    def children(self) -> List["Node"]:
        """子ノードのリストを取得"""
        return self._children.copy()

    @property
    def position(self) -> Tuple[int, int]:
        """ノードの位置(x, y)を取得"""
        return self._position

    @property
    def font_size(self) -> Optional[int]:
        """フォントサイズを取得"""
        return self._font_size

    @font_size.setter
    def font_size(self, value: Optional[int]) -> None:
        """フォントサイズを設定"""
        self._font_size = value

    @property
    def font_color(self) -> Optional[str]:
        """フォント色を取得"""
        return self._font_color

    @font_color.setter
    def font_color(self, value: Optional[str]) -> None:
        """フォント色を設定"""
        self._font_color = value

    def add_child(self, child: "Node") -> None:
        """
        子ノードを追加する

        既に他の親を持つ子ノードの場合、古い親から削除してから追加する

        Args:
            child: 追加する子ノード
        """
        # 既に他の親を持つ場合は、古い親から削除
        if child._parent is not None:
            child._parent._children.remove(child)

        # 新しい親子関係を設定
        if child not in self._children:
            self._children.append(child)
        child._parent = self

    def remove_child(self, child: "Node") -> None:
        """
        子ノードを削除する

        Args:
            child: 削除する子ノード
        """
        if child in self._children:
            self._children.remove(child)
            child._parent = None

    def set_position(self, x: int, y: int) -> None:
        """
        ノードの位置を設定する

        Args:
            x: X座標
            y: Y座標
        """
        self._position = (x, y)

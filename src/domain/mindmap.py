"""
MindMapドメインモデル

マインドマップ全体を管理するクラス
"""
from typing import Optional, List
from src.domain.node import Node


class MindMap:
    """マインドマップ全体を表すクラス"""

    def __init__(self, title: str = "Untitled") -> None:
        """
        マインドマップを初期化する

        Args:
            title: マインドマップのタイトル（デフォルト: "Untitled"）
        """
        self._title: str = title
        self._root: Optional[Node] = None

    @property
    def title(self) -> str:
        """マインドマップのタイトルを取得"""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        """マインドマップのタイトルを設定"""
        self._title = value

    @property
    def root(self) -> Optional[Node]:
        """ルートノードを取得"""
        return self._root

    def set_root(self, node: Node) -> None:
        """
        ルートノードを設定する

        Args:
            node: ルートノードとして設定するノード
        """
        self._root = node

    def get_all_nodes(self) -> List[Node]:
        """
        マインドマップ内の全ノードを取得する

        Returns:
            全ノードのリスト（深さ優先探索順）
        """
        if self._root is None:
            return []

        nodes: List[Node] = []
        self._collect_nodes(self._root, nodes)
        return nodes

    def _collect_nodes(self, node: Node, nodes: List[Node]) -> None:
        """
        ノードを再帰的に収集する（深さ優先探索）

        Args:
            node: 現在のノード
            nodes: ノードを格納するリスト
        """
        nodes.append(node)
        for child in node.children:
            self._collect_nodes(child, nodes)

    def find_node_by_id(self, node_id: str) -> Optional[Node]:
        """
        IDでノードを検索する

        Args:
            node_id: 検索するノードのID

        Returns:
            見つかったノード、見つからない場合はNone
        """
        all_nodes = self.get_all_nodes()
        for node in all_nodes:
            if node.id == node_id:
                return node
        return None

    def clear(self) -> None:
        """マインドマップをクリアする（全ノードを削除）"""
        self._root = None

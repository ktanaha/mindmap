"""
NodeツリーからMarkdownテキストへの変換

マインドマップのNodeツリーをMarkdownのリスト表記に変換する
"""
from typing import Optional, List
from src.domain.node import Node


class TreeToMarkdownConverter:
    """NodeツリーをMarkdownテキストに変換するクラス"""

    def __init__(self) -> None:
        """コンバーターを初期化する"""
        pass

    def convert(self, root: Optional[Node]) -> str:
        """
        NodeツリーをMarkdownテキストに変換する

        Args:
            root: ルートノード

        Returns:
            Markdownテキスト（リスト形式）
        """
        if root is None:
            return ""

        lines: List[str] = []

        # 仮想ルートノードの場合は、子ノードを直接depth 0で変換
        if root.text == "__virtual_root__":
            for child in root.children:
                self._convert_node(child, 0, lines)
        else:
            self._convert_node(root, 0, lines)

        return "\n".join(lines)

    def _convert_node(self, node: Node, depth: int, lines: List[str]) -> None:
        """
        ノードを再帰的にMarkdown行に変換

        Args:
            node: 変換するノード
            depth: 現在の深さ（インデントレベル）
            lines: 出力行のリスト
        """
        # インデント（スペース2つ x depth）
        indent = "  " * depth
        # リスト項目として追加
        lines.append(f"{indent}- {node.text}")

        # 子ノードを再帰的に変換
        for child in node.children:
            self._convert_node(child, depth + 1, lines)

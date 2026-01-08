"""
MarkdownParser

MarkdownテキストをNodeツリー構造に変換するパーサー
"""
import re
from typing import Optional, List, Tuple
from src.domain.node import Node


class MarkdownParser:
    """Markdownテキストをパースしてノードツリーを生成するクラス"""

    def __init__(self) -> None:
        """パーサーを初期化する"""
        # 見出しパターン: # 見出し
        self._heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        # リストパターン: - または * で始まる（インデント考慮）
        self._list_pattern = re.compile(r'^(\s*)[-*]\s+(.+)$')
        # 行番号→ノードのマッピング
        self._line_to_node_map: dict[int, Node] = {}

    def parse(self, markdown_text: str) -> Optional[Node]:
        """
        Markdownテキストをパースしてノードツリーを生成する

        Args:
            markdown_text: Markdownテキスト

        Returns:
            ルートノード、空の場合はNone
        """
        # マッピングをクリア
        self._line_to_node_map.clear()

        if not markdown_text.strip():
            return None

        # リスト表記を優先的にチェック
        items = self._extract_list_items(markdown_text)
        if items:
            return self._build_tree_from_list(items)

        # リスト表記がない場合は見出し表記をチェック
        headings = self._extract_headings(markdown_text)
        if not headings:
            return None

        return self._build_tree(headings)

    def _extract_headings(self, markdown_text: str) -> List[Tuple[int, str, int]]:
        """
        Markdownテキストから見出しを抽出する

        Args:
            markdown_text: Markdownテキスト

        Returns:
            (レベル, テキスト, 行番号)のタプルのリスト
        """
        headings: List[Tuple[int, str, int]] = []
        lines = markdown_text.split('\n')

        for line_num, line in enumerate(lines):
            match = self._heading_pattern.match(line)
            if match:
                level = len(match.group(1))  # #の数
                text = match.group(2).strip()
                headings.append((level, text, line_num))

        return headings

    def _extract_list_items(self, markdown_text: str) -> List[Tuple[int, str, int]]:
        """
        Markdownテキストからリスト項目を抽出する

        Args:
            markdown_text: Markdownテキスト

        Returns:
            (インデントレベル, テキスト, 行番号)のタプルのリスト
        """
        items: List[Tuple[int, str, int]] = []
        lines = markdown_text.split('\n')

        for line_num, line in enumerate(lines):
            match = self._list_pattern.match(line)
            if match:
                indent = match.group(1)
                # インデントレベルを計算（2スペースまたは1タブ = 1レベル）
                indent_level = len(indent.replace('\t', '  ')) // 2
                text = match.group(2).strip()
                items.append((indent_level, text, line_num))

        return items

    def _build_tree_from_list(self, items: List[Tuple[int, str, int]]) -> Optional[Node]:
        """
        リスト項目からノードツリーを構築する

        Args:
            items: (インデントレベル, テキスト, 行番号)のタプルのリスト

        Returns:
            ルートノード
        """
        if not items:
            return None

        # 最小のインデントレベルを探す
        min_level = min(level for level, _, _ in items)

        # 最小レベルの項目を集める
        top_level_items = [(level, text, line_num) for level, text, line_num in items if level == min_level]

        # 最上位レベルが複数ある場合、仮想ルートノードを作成
        if len(top_level_items) > 1:
            root = Node(text="__virtual_root__")
            # すべての項目を仮想ルートの下に配置するため、レベルを調整
            adjusted_items = [(level - min_level, text, line_num) for level, text, line_num in items]
            level_stack = {-1: root}  # 仮想ルートをレベル-1に配置

            for level, text, line_num in adjusted_items:
                new_node = Node(text=text)
                # 行番号とノードをマッピング
                self._line_to_node_map[line_num] = new_node

                # 親となるノードを探す
                parent = self._find_parent(level, level_stack)

                if parent:
                    parent.add_child(new_node)
                else:
                    root.add_child(new_node)

                # 現在のレベル以上のレベルをスタックから削除
                keys_to_remove = [k for k in level_stack.keys() if k >= level]
                for k in keys_to_remove:
                    del level_stack[k]

                # 新しいノードをスタックに追加
                level_stack[level] = new_node

            return root
        else:
            # 最上位レベルが1つの場合は従来通り
            root_level, root_text, root_line_num = items[0]
            root = Node(text=root_text)
            # 行番号とノードをマッピング
            self._line_to_node_map[root_line_num] = root

            # スタックで現在の各レベルでの最新ノードを追跡
            level_stack = {root_level: root}

            for level, text, line_num in items[1:]:
                new_node = Node(text=text)
                # 行番号とノードをマッピング
                self._line_to_node_map[line_num] = new_node

                # 親となるノードを探す（現在のレベルより小さい最大のレベル）
                parent = self._find_parent(level, level_stack)

                if parent:
                    parent.add_child(new_node)
                else:
                    # 親が見つからない場合はルートの子とする
                    root.add_child(new_node)

                # 現在のレベル以上のレベルをスタックから削除
                keys_to_remove = [k for k in level_stack.keys() if k >= level]
                for k in keys_to_remove:
                    del level_stack[k]

                # 新しいノードをスタックに追加
                level_stack[level] = new_node

            return root

    def _build_tree(self, headings: List[Tuple[int, str, int]]) -> Optional[Node]:
        """
        見出しリストからノードツリーを構築する

        Args:
            headings: (レベル, テキスト, 行番号)のタプルのリスト

        Returns:
            ルートノード
        """
        if not headings:
            return None

        # 最小の見出しレベルを探す
        min_level = min(level for level, _, _ in headings)

        # 最小レベルの見出しを集める
        top_level_headings = [(level, text, line_num) for level, text, line_num in headings if level == min_level]

        # 最上位レベルが複数ある場合、仮想ルートノードを作成
        if len(top_level_headings) > 1:
            root = Node(text="__virtual_root__")
            # すべての見出しを仮想ルートの下に配置するため、レベルを調整
            adjusted_headings = [(level - min_level + 1, text, line_num) for level, text, line_num in headings]
            level_stack = {0: root}  # 仮想ルートをレベル0に配置

            for level, text, line_num in adjusted_headings:
                new_node = Node(text=text)
                # 行番号とノードをマッピング
                self._line_to_node_map[line_num] = new_node

                # 親となるノードを探す
                parent = self._find_parent(level, level_stack)

                if parent:
                    parent.add_child(new_node)
                else:
                    root.add_child(new_node)

                # 現在のレベル以上のレベルをスタックから削除
                keys_to_remove = [k for k in level_stack.keys() if k >= level]
                for k in keys_to_remove:
                    del level_stack[k]

                # 新しいノードをスタックに追加
                level_stack[level] = new_node

            return root
        else:
            # 最上位レベルが1つの場合は従来通り
            root_level, root_text, root_line_num = headings[0]
            root = Node(text=root_text)
            # 行番号とノードをマッピング
            self._line_to_node_map[root_line_num] = root

            # スタックで現在の各レベルでの最新ノードを追跡
            # level -> node のマッピング
            level_stack = {root_level: root}

            for level, text, line_num in headings[1:]:
                new_node = Node(text=text)
                # 行番号とノードをマッピング
                self._line_to_node_map[line_num] = new_node

                # 親となるノードを探す（現在のレベルより小さい最大のレベル）
                parent = self._find_parent(level, level_stack)

                if parent:
                    parent.add_child(new_node)
                else:
                    # 親が見つからない場合はルートの子とする
                    root.add_child(new_node)

                # 現在のレベルとそれ以下のレベルをスタックから削除
                keys_to_remove = [k for k in level_stack.keys() if k >= level]
                for k in keys_to_remove:
                    del level_stack[k]

                # 新しいノードをスタックに追加
                level_stack[level] = new_node

            return root

    def get_node_by_line(self, line_number: int) -> Optional[Node]:
        """
        行番号からノードを検索する

        Args:
            line_number: 行番号（0始まり）

        Returns:
            対応するNode、見つからない場合はNone
        """
        return self._line_to_node_map.get(line_number)

    def get_line_by_node(self, node: Node) -> Optional[int]:
        """
        ノードから行番号を検索する

        Args:
            node: ノード

        Returns:
            対応する行番号（0始まり）、見つからない場合はNone
        """
        for line_num, n in self._line_to_node_map.items():
            if n == node:
                return line_num
        return None

    def _find_parent(self, level: int, level_stack: dict) -> Optional[Node]:
        """
        指定されたレベルのノードの親を探す

        Args:
            level: 検索するレベル
            level_stack: レベルとノードのマッピング

        Returns:
            親ノード、見つからない場合はNone
        """
        # 現在のレベルより小さいレベルを探す
        parent_levels = [l for l in level_stack.keys() if l < level]
        if not parent_levels:
            return None

        # 最も大きいレベル（最も近い親）を選択
        parent_level = max(parent_levels)
        return level_stack[parent_level]

"""
TreeToMarkdownConverterのテスト
"""
import pytest
from src.parser.tree_to_markdown import TreeToMarkdownConverter
from src.domain.node import Node


class TestTreeToMarkdownConverter:
    """TreeToMarkdownConverterのテストクラス"""

    @pytest.fixture
    def converter(self):
        """コンバーターのフィクスチャ"""
        return TreeToMarkdownConverter()

    def test_convert_none(self, converter):
        """Noneを変換すると空文字列を返す"""
        result = converter.convert(None)
        assert result == ""

    def test_convert_single_node(self, converter):
        """単一ノードを変換"""
        root = Node(text="ルート")
        result = converter.convert(root)
        assert result == "- ルート"

    def test_convert_with_children(self, converter):
        """子ノードを持つツリーを変換"""
        root = Node(text="プロジェクト")
        child1 = Node(text="フェーズ1")
        child2 = Node(text="フェーズ2")
        root.add_child(child1)
        root.add_child(child2)

        result = converter.convert(root)
        expected = """- プロジェクト
  - フェーズ1
  - フェーズ2"""
        assert result == expected

    def test_convert_nested_tree(self, converter):
        """ネストしたツリーを変換"""
        root = Node(text="プロジェクト計画")
        phase1 = Node(text="フェーズ1：設計")
        phase2 = Node(text="フェーズ2：実装")
        task1 = Node(text="要件定義")
        task2 = Node(text="UI設計")

        root.add_child(phase1)
        root.add_child(phase2)
        phase1.add_child(task1)
        phase1.add_child(task2)

        result = converter.convert(root)
        expected = """- プロジェクト計画
  - フェーズ1：設計
    - 要件定義
    - UI設計
  - フェーズ2：実装"""
        assert result == expected

    def test_convert_deep_nesting(self, converter):
        """深いネスト構造を変換"""
        root = Node(text="Level 0")
        level1 = Node(text="Level 1")
        level2 = Node(text="Level 2")
        level3 = Node(text="Level 3")

        root.add_child(level1)
        level1.add_child(level2)
        level2.add_child(level3)

        result = converter.convert(root)
        expected = """- Level 0
  - Level 1
    - Level 2
      - Level 3"""
        assert result == expected

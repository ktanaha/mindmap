"""
MarkdownParserクラスのテスト

MarkdownテキストをNodeツリー構造に変換する
"""
import pytest
from src.parser.markdown_parser import MarkdownParser
from src.domain.node import Node


class TestMarkdownParserBasic:
    """基本的なパース機能のテスト"""

    def test_parse_empty_text(self):
        """空のテキストはNoneを返す"""
        parser = MarkdownParser()
        result = parser.parse("")
        assert result is None

    def test_parse_single_heading(self):
        """単一の見出しをパースできる"""
        parser = MarkdownParser()
        markdown = "# ルート"
        root = parser.parse(markdown)

        assert root is not None
        assert root.text == "ルート"
        assert len(root.children) == 0

    def test_parse_multiple_h1_headings(self):
        """複数のH1見出しは最初のものだけがルートになる"""
        parser = MarkdownParser()
        markdown = """# ルート1
# ルート2"""
        root = parser.parse(markdown)

        assert root is not None
        assert root.text == "ルート1"


class TestMarkdownParserHierarchy:
    """階層構造のパースのテスト"""

    def test_parse_parent_child(self):
        """親子関係をパースできる"""
        parser = MarkdownParser()
        markdown = """# 親
## 子"""
        root = parser.parse(markdown)

        assert root.text == "親"
        assert len(root.children) == 1
        assert root.children[0].text == "子"

    def test_parse_three_levels(self):
        """3階層の構造をパースできる"""
        parser = MarkdownParser()
        markdown = """# ルート
## 子
### 孫"""
        root = parser.parse(markdown)

        assert root.text == "ルート"
        assert len(root.children) == 1

        child = root.children[0]
        assert child.text == "子"
        assert len(child.children) == 1

        grandchild = child.children[0]
        assert grandchild.text == "孫"

    def test_parse_multiple_children(self):
        """同じレベルの複数の子をパースできる"""
        parser = MarkdownParser()
        markdown = """# ルート
## 子1
## 子2
## 子3"""
        root = parser.parse(markdown)

        assert root.text == "ルート"
        assert len(root.children) == 3
        assert root.children[0].text == "子1"
        assert root.children[1].text == "子2"
        assert root.children[2].text == "子3"

    def test_parse_complex_hierarchy(self):
        """複雑な階層構造をパースできる"""
        parser = MarkdownParser()
        markdown = """# ルート
## 子1
### 孫1-1
### 孫1-2
## 子2
### 孫2-1"""
        root = parser.parse(markdown)

        assert root.text == "ルート"
        assert len(root.children) == 2

        child1 = root.children[0]
        assert child1.text == "子1"
        assert len(child1.children) == 2
        assert child1.children[0].text == "孫1-1"
        assert child1.children[1].text == "孫1-2"

        child2 = root.children[1]
        assert child2.text == "子2"
        assert len(child2.children) == 1
        assert child2.children[0].text == "孫2-1"


class TestMarkdownParserEdgeCases:
    """エッジケースのテスト"""

    def test_parse_heading_with_extra_spaces(self):
        """余分なスペースを含む見出しをパースできる"""
        parser = MarkdownParser()
        markdown = "#   スペース多め   "
        root = parser.parse(markdown)

        assert root.text == "スペース多め"

    def test_parse_skip_non_heading_lines(self):
        """見出し以外の行はスキップする"""
        parser = MarkdownParser()
        markdown = """# ルート
これは本文です
## 子
本文2"""
        root = parser.parse(markdown)

        assert root.text == "ルート"
        assert len(root.children) == 1
        assert root.children[0].text == "子"

    def test_parse_heading_level_skip(self):
        """見出しレベルが飛んでいても処理できる"""
        parser = MarkdownParser()
        markdown = """# ルート
### 孫（レベル飛ばし）"""
        root = parser.parse(markdown)

        assert root.text == "ルート"
        # レベルが飛んでいる場合は直接の子として扱う
        assert len(root.children) == 1
        assert root.children[0].text == "孫（レベル飛ばし）"

    def test_parse_h2_without_h1(self):
        """H1がなくH2から始まる場合"""
        parser = MarkdownParser()
        markdown = """## 子から始まる"""
        root = parser.parse(markdown)

        # H2をルートとして扱う
        assert root is not None
        assert root.text == "子から始まる"


class TestMarkdownParserListNotation:
    """リスト表記のパースのテスト"""

    def test_parse_simple_list(self):
        """シンプルなリストをパースできる"""
        parser = MarkdownParser()
        markdown = """- ルート
  - 子1
  - 子2"""
        root = parser.parse(markdown)

        assert root.text == "ルート"
        assert len(root.children) == 2
        assert root.children[0].text == "子1"
        assert root.children[1].text == "子2"

    def test_parse_nested_list(self):
        """ネストしたリストをパースできる"""
        parser = MarkdownParser()
        markdown = """- プロジェクト計画
  - フェーズ1：設計
    - 要件定義
    - UI設計
  - フェーズ2：実装
    - バックエンド開発
    - フロントエンド開発
  - フェーズ3：テスト"""
        root = parser.parse(markdown)

        assert root.text == "プロジェクト計画"
        assert len(root.children) == 3

        phase1 = root.children[0]
        assert phase1.text == "フェーズ1：設計"
        assert len(phase1.children) == 2
        assert phase1.children[0].text == "要件定義"
        assert phase1.children[1].text == "UI設計"

        phase2 = root.children[1]
        assert phase2.text == "フェーズ2：実装"
        assert len(phase2.children) == 2

        phase3 = root.children[2]
        assert phase3.text == "フェーズ3：テスト"

    def test_parse_asterisk_list(self):
        """アスタリスク（*）のリストもパースできる"""
        parser = MarkdownParser()
        markdown = """* ルート
  * 子1
  * 子2"""
        root = parser.parse(markdown)

        assert root.text == "ルート"
        assert len(root.children) == 2

    def test_parse_mixed_markers(self):
        """- と * が混在していてもパースできる"""
        parser = MarkdownParser()
        markdown = """- ルート
  * 子1
  - 子2"""
        root = parser.parse(markdown)

        assert root.text == "ルート"
        assert len(root.children) == 2

"""
MindMapクラスのテスト

MindMapはマインドマップ全体を管理するドメインモデル
"""
import pytest
from src.domain.node import Node
from src.domain.mindmap import MindMap


class TestMindMapCreation:
    """マインドマップの作成に関するテスト"""

    def test_create_empty_mindmap(self):
        """空のマインドマップを作成できる"""
        mindmap = MindMap()
        assert mindmap is not None

    def test_create_mindmap_with_no_root(self):
        """新規作成されたマインドマップはルートノードを持たない"""
        mindmap = MindMap()
        assert mindmap.root is None

    def test_create_mindmap_with_title(self):
        """タイトル付きでマインドマップを作成できる"""
        mindmap = MindMap(title="学習ノート")
        assert mindmap.title == "学習ノート"

    def test_create_mindmap_with_default_title(self):
        """デフォルトタイトルでマインドマップを作成できる"""
        mindmap = MindMap()
        assert mindmap.title == "Untitled"


class TestMindMapRoot:
    """ルートノードに関するテスト"""

    def test_set_root_node(self):
        """ルートノードを設定できる"""
        mindmap = MindMap()
        root = Node(text="ルート")
        mindmap.set_root(root)
        assert mindmap.root == root

    def test_replace_root_node(self):
        """ルートノードを置き換えできる"""
        mindmap = MindMap()
        old_root = Node(text="旧ルート")
        new_root = Node(text="新ルート")

        mindmap.set_root(old_root)
        mindmap.set_root(new_root)

        assert mindmap.root == new_root
        assert mindmap.root != old_root


class TestMindMapNodeManagement:
    """ノード管理に関するテスト"""

    def test_get_all_nodes_empty(self):
        """空のマインドマップは空のノードリストを返す"""
        mindmap = MindMap()
        nodes = mindmap.get_all_nodes()
        assert len(nodes) == 0

    def test_get_all_nodes_with_root_only(self):
        """ルートのみのマインドマップは1つのノードを返す"""
        mindmap = MindMap()
        root = Node(text="ルート")
        mindmap.set_root(root)

        nodes = mindmap.get_all_nodes()
        assert len(nodes) == 1
        assert root in nodes

    def test_get_all_nodes_with_hierarchy(self):
        """階層構造を持つマインドマップは全ノードを返す"""
        mindmap = MindMap()
        root = Node(text="ルート")
        child1 = Node(text="子1")
        child2 = Node(text="子2")
        grandchild = Node(text="孫")

        root.add_child(child1)
        root.add_child(child2)
        child1.add_child(grandchild)
        mindmap.set_root(root)

        nodes = mindmap.get_all_nodes()
        assert len(nodes) == 4
        assert root in nodes
        assert child1 in nodes
        assert child2 in nodes
        assert grandchild in nodes

    def test_find_node_by_id(self):
        """IDでノードを検索できる"""
        mindmap = MindMap()
        root = Node(text="ルート")
        child1 = Node(text="子1")
        child2 = Node(text="子2")

        root.add_child(child1)
        root.add_child(child2)
        mindmap.set_root(root)

        found = mindmap.find_node_by_id(child1.id)
        assert found == child1

    def test_find_node_by_id_not_found(self):
        """存在しないIDで検索するとNoneを返す"""
        mindmap = MindMap()
        root = Node(text="ルート")
        mindmap.set_root(root)

        found = mindmap.find_node_by_id("non-existent-id")
        assert found is None


class TestMindMapTitle:
    """タイトル管理に関するテスト"""

    def test_update_title(self):
        """マインドマップのタイトルを更新できる"""
        mindmap = MindMap(title="初期タイトル")
        mindmap.title = "更新後のタイトル"
        assert mindmap.title == "更新後のタイトル"


class TestMindMapClear:
    """クリアに関するテスト"""

    def test_clear_mindmap(self):
        """マインドマップをクリアできる"""
        mindmap = MindMap(title="テスト")
        root = Node(text="ルート")
        child = Node(text="子")
        root.add_child(child)
        mindmap.set_root(root)

        mindmap.clear()

        assert mindmap.root is None
        assert len(mindmap.get_all_nodes()) == 0

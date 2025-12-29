"""
Nodeクラスのテスト

Nodeはマインドマップの各ノード（節点）を表すドメインモデル
"""
import pytest
from src.domain.node import Node


class TestNodeCreation:
    """ノードの作成に関するテスト"""

    def test_create_node_with_text(self):
        """テキストを指定してノードを作成できる"""
        node = Node(text="ルートノード")
        assert node.text == "ルートノード"

    def test_create_node_has_unique_id(self):
        """各ノードは一意のIDを持つ"""
        node1 = Node(text="ノード1")
        node2 = Node(text="ノード2")
        assert node1.id != node2.id
        assert node1.id is not None
        assert node2.id is not None

    def test_create_node_with_no_parent(self):
        """新規作成されたノードは親を持たない"""
        node = Node(text="ノード")
        assert node.parent is None

    def test_create_node_with_empty_children(self):
        """新規作成されたノードは子を持たない"""
        node = Node(text="ノード")
        assert len(node.children) == 0

    def test_create_node_with_default_position(self):
        """新規作成されたノードはデフォルト位置(0, 0)を持つ"""
        node = Node(text="ノード")
        assert node.position == (0, 0)


class TestNodeHierarchy:
    """ノードの階層構造に関するテスト"""

    def test_add_child_node(self):
        """子ノードを追加できる"""
        parent = Node(text="親")
        child = Node(text="子")
        parent.add_child(child)

        assert len(parent.children) == 1
        assert parent.children[0] == child
        assert child.parent == parent

    def test_add_multiple_children(self):
        """複数の子ノードを追加できる"""
        parent = Node(text="親")
        child1 = Node(text="子1")
        child2 = Node(text="子2")
        child3 = Node(text="子3")

        parent.add_child(child1)
        parent.add_child(child2)
        parent.add_child(child3)

        assert len(parent.children) == 3
        assert child1 in parent.children
        assert child2 in parent.children
        assert child3 in parent.children

    def test_remove_child_node(self):
        """子ノードを削除できる"""
        parent = Node(text="親")
        child = Node(text="子")
        parent.add_child(child)

        parent.remove_child(child)

        assert len(parent.children) == 0
        assert child.parent is None

    def test_change_parent(self):
        """ノードの親を変更できる"""
        old_parent = Node(text="旧親")
        new_parent = Node(text="新親")
        child = Node(text="子")

        old_parent.add_child(child)
        new_parent.add_child(child)

        assert child.parent == new_parent
        assert child not in old_parent.children
        assert child in new_parent.children


class TestNodePosition:
    """ノードの位置に関するテスト"""

    def test_set_position(self):
        """ノードの位置を設定できる"""
        node = Node(text="ノード")
        node.set_position(100, 200)
        assert node.position == (100, 200)

    def test_update_position(self):
        """ノードの位置を更新できる"""
        node = Node(text="ノード")
        node.set_position(100, 200)
        node.set_position(300, 400)
        assert node.position == (300, 400)


class TestNodeText:
    """ノードのテキストに関するテスト"""

    def test_update_text(self):
        """ノードのテキストを更新できる"""
        node = Node(text="初期テキスト")
        node.text = "更新後のテキスト"
        assert node.text == "更新後のテキスト"

    def test_empty_text(self):
        """空のテキストでノードを作成できる"""
        node = Node(text="")
        assert node.text == ""

"""
メインウィンドウ

アプリケーションのメインウィンドウ
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from src.presentation.markdown_editor import MarkdownEditor
from src.presentation.mindmap_view import MindMapView
from src.parser.markdown_parser import MarkdownParser
from src.parser.tree_to_markdown import TreeToMarkdownConverter
from src.domain.mindmap import MindMap
from src.domain.node import Node
from pathlib import Path


class MainWindow(QMainWindow):
    """メインウィンドウクラス"""

    def __init__(self) -> None:
        """メインウィンドウを初期化する"""
        super().__init__()

        # ドメインモデル
        self._mindmap = MindMap()
        self._parser = MarkdownParser()
        self._converter = TreeToMarkdownConverter()
        self._current_file: Path | None = None
        self._updating_from_drag = False  # ドラッグ更新中フラグ

        # UI初期化
        self._setup_ui()
        self._create_menu()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """UIをセットアップする"""
        self.setWindowTitle("MindMap - Untitled")
        self.setGeometry(100, 100, 1400, 800)

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # レイアウト
        layout = QHBoxLayout(central_widget)

        # スプリッター（2ペイン）
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左ペイン: Markdownエディタ
        self._editor = MarkdownEditor()
        splitter.addWidget(self._editor)

        # 右ペイン: マインドマップビュー
        self._mindmap_view = MindMapView()
        splitter.addWidget(self._mindmap_view)

        # スプリッターの初期サイズ比率（1:1）
        splitter.setSizes([700, 700])

        layout.addWidget(splitter)

    def _create_menu(self) -> None:
        """メニューバーを作成する"""
        menubar = self.menuBar()

        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル(&F)")

        # 新規
        new_action = QAction("新規(&N)", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._on_new)
        file_menu.addAction(new_action)

        # 開く
        open_action = QAction("開く(&O)...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        # 保存
        save_action = QAction("保存(&S)", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        # 名前を付けて保存
        save_as_action = QAction("名前を付けて保存(&A)...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._on_save_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # 終了
        exit_action = QAction("終了(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _connect_signals(self) -> None:
        """シグナルを接続する"""
        # エディタのテキスト変更時にマインドマップを更新
        self._editor.text_changed.connect(self._on_text_changed)

        # ノードが付け替えられたときにMarkdownを更新
        self._mindmap_view.node_reparented.connect(self._on_node_reparented)

    def _on_text_changed(self, text: str) -> None:
        """
        テキスト変更時の処理

        Args:
            text: 変更後のテキスト
        """
        # ドラッグ更新中は無視（無限ループ防止）
        if self._updating_from_drag:
            return

        # Markdownをパース
        root = self._parser.parse(text)

        # マインドマップを更新
        self._mindmap.set_root(root)
        if root:
            self._mindmap.title = root.text

        # ビューを更新
        self._mindmap_view.display_tree(root)

    def _on_node_reparented(self, dropped_node: Node, target_node: Node) -> None:
        """
        ノードが付け替えられたときの処理

        Args:
            dropped_node: ドロップされたノード
            target_node: ドロップ先のノード
        """
        # ドラッグ更新中フラグを設定
        self._updating_from_drag = True

        # ノードツリーをMarkdownテキストに変換
        root = self._mindmap.root
        markdown_text = self._converter.convert(root)

        # エディタを更新
        self._editor.set_text(markdown_text)

        # フラグをリセット
        self._updating_from_drag = False

    def _on_new(self) -> None:
        """新規作成"""
        self._editor.set_text("")
        self._mindmap.clear()
        self._current_file = None
        self.setWindowTitle("MindMap - Untitled")

    def _on_open(self) -> None:
        """ファイルを開く"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "ファイルを開く",
            "",
            "Markdown Files (*.md);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    markdown_text = f.read()
                    self._editor.set_text(markdown_text)
                    self._current_file = Path(file_path)
                    self.setWindowTitle(f"MindMap - {self._current_file.name}")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"ファイルを開けませんでした:\n{e}")

    def _on_save(self) -> None:
        """保存"""
        if self._current_file:
            self._save_to_file(self._current_file)
        else:
            self._on_save_as()

    def _on_save_as(self) -> None:
        """名前を付けて保存"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "名前を付けて保存",
            "untitled.md",
            "Markdown Files (*.md);;All Files (*)"
        )

        if file_path:
            # 拡張子がない場合は.mdを追加
            file_path_obj = Path(file_path)
            if not file_path_obj.suffix:
                file_path_obj = file_path_obj.with_suffix('.md')

            self._current_file = file_path_obj
            self._save_to_file(self._current_file)
            self.setWindowTitle(f"MindMap - {self._current_file.name}")

    def _save_to_file(self, file_path: Path) -> None:
        """
        ファイルに保存

        Args:
            file_path: 保存先ファイルパス
        """
        try:
            markdown_text = self._editor.get_text()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"保存できませんでした:\n{e}")

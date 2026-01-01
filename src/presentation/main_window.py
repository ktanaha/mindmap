"""
メインウィンドウ

アプリケーションのメインウィンドウ
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QColor
from src.presentation.markdown_editor import MarkdownEditor
from src.presentation.mindmap_view import MindMapView
from src.presentation.settings_dialog import SettingsDialog
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

        # 設定
        self._settings = QSettings("MindMap", "MindMapApp")
        self._load_settings()

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
        self._mindmap_view = MindMapView(
            font_size=self._font_size,
            font_color=self._font_color,
            line_color=self._line_color,
            layout_direction=self._layout_direction
        )
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

        # 編集メニュー
        edit_menu = menubar.addMenu("編集(&E)")

        # 設定
        settings_action = QAction("設定(&P)...", self)
        settings_action.triggered.connect(self._on_settings)
        edit_menu.addAction(settings_action)

    def _connect_signals(self) -> None:
        """シグナルを接続する"""
        # エディタのテキスト変更時にマインドマップを更新
        self._editor.text_changed.connect(self._on_text_changed)

        # カーソル位置変更時に対応するノードを中心に表示
        self._editor.cursor_line_changed.connect(self._on_cursor_line_changed)

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

    def _on_cursor_line_changed(self, line_number: int) -> None:
        """
        カーソル位置変更時の処理

        Args:
            line_number: カーソルがある行番号（0始まり）
        """
        # 行番号から対応するノードを検索
        node = self._parser.get_node_by_line(line_number)
        if node is not None:
            # ノードを中心に表示
            self._mindmap_view.center_on_node(node)

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

    def _load_settings(self) -> None:
        """設定を読み込む"""
        # デフォルト値
        self._font_size = self._settings.value("font_size", 14, type=int)

        # 色の読み込み（デフォルトは黒）
        color_name = self._settings.value("font_color", "#000000", type=str)
        self._font_color = QColor(color_name)

        # 線の色の読み込み（デフォルトはグレー）
        line_color_name = self._settings.value("line_color", "#969696", type=str)
        self._line_color = QColor(line_color_name)

        # レイアウト方向の読み込み（デフォルトは右のみ）
        self._layout_direction = self._settings.value("layout_direction", 0, type=int)

    def _save_settings(self) -> None:
        """設定を保存する"""
        self._settings.setValue("font_size", self._font_size)
        self._settings.setValue("font_color", self._font_color.name())
        self._settings.setValue("line_color", self._line_color.name())
        self._settings.setValue("layout_direction", self._layout_direction)

    def _on_settings(self) -> None:
        """設定ダイアログを開く"""
        dialog = SettingsDialog(self)
        dialog.set_font_size(self._font_size)
        dialog.set_font_color(self._font_color)
        dialog.set_line_color(self._line_color)
        dialog.set_layout_direction(self._layout_direction)

        if dialog.exec():
            # 設定を取得
            new_font_size = dialog.get_font_size()
            new_font_color = dialog.get_font_color()
            new_line_color = dialog.get_line_color()
            new_layout_direction = dialog.get_layout_direction()
            apply_scope = dialog.get_apply_scope()

            # 適用範囲に応じて設定を適用
            selected_node = self._mindmap_view.get_selected_node()

            if apply_scope == 0:
                # 全体に適用
                self._font_size = new_font_size
                self._font_color = new_font_color
                self._line_color = new_line_color
                self._layout_direction = new_layout_direction
                self._save_settings()

                # マインドマップビューのデフォルト設定を更新
                self._mindmap_view.set_font_size(new_font_size)
                self._mindmap_view.set_font_color(new_font_color)
                self._mindmap_view.set_line_color(new_line_color)
                self._mindmap_view.set_layout_direction(new_layout_direction)

            elif apply_scope == 1:
                # 選択中のノードのみ
                if selected_node is not None:
                    selected_node.font_size = new_font_size
                    selected_node.font_color = new_font_color.name()
                else:
                    QMessageBox.warning(self, "警告", "ノードが選択されていません")
                    return

            elif apply_scope == 2:
                # 選択中のノード以下すべて
                if selected_node is not None:
                    self._apply_settings_to_subtree(selected_node, new_font_size, new_font_color.name())
                else:
                    QMessageBox.warning(self, "警告", "ノードが選択されていません")
                    return

            # ビューを再描画
            root = self._mindmap.root
            self._mindmap_view.display_tree(root)

    def _apply_settings_to_subtree(self, node: Node, font_size: int, font_color: str) -> None:
        """
        ノードとその子孫すべてに設定を適用する

        Args:
            node: ルートとなるノード
            font_size: フォントサイズ
            font_color: フォント色（カラーコード）
        """
        node.font_size = font_size
        node.font_color = font_color

        for child in node.children:
            self._apply_settings_to_subtree(child, font_size, font_color)

"""
メインウィンドウ

アプリケーションのメインウィンドウ
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QFileDialog, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt, QSettings, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QAction, QColor, QIcon
from src.presentation.markdown_editor import MarkdownEditor
from src.presentation.mindmap_view import MindMapView
from src.presentation.settings_dialog import SettingsDialog
from src.parser.markdown_parser import MarkdownParser
from src.parser.tree_to_markdown import TreeToMarkdownConverter
from src.domain.mindmap import MindMap
from src.domain.node import Node
from pathlib import Path
from datetime import datetime


class MainWindow(QMainWindow):
    """メインウィンドウクラス"""

    def __init__(self) -> None:
        """メインウィンドウを初期化する"""
        super().__init__()

        # 設定
        self._settings = QSettings("OYUWAKU", "OYUWAKUApp")
        self._load_settings()

        # ドメインモデル
        self._mindmap = MindMap()
        self._parser = MarkdownParser()
        self._converter = TreeToMarkdownConverter()
        self._current_file: Path | None = None
        self._updating_from_drag = False  # ドラッグ更新中フラグ
        self._has_unsaved_changes = False  # 未保存の変更があるかどうか

        # 自動保存タイマー（5秒間操作がない場合に自動保存）
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(5000)  # 5秒
        self._autosave_timer.setSingleShot(True)  # 1回のみ実行
        self._autosave_timer.timeout.connect(self._auto_save)

        # 最近開いたファイルのリスト
        self._recent_files: list[str] = []
        self._recent_files_actions: list[QAction] = []
        self._max_recent_files = 10
        self._recent_files_path = Path.home() / ".oyuwaku_recent_files.txt"

        # ファイル履歴ログ
        self._log_file_path = Path.home() / ".oyuwaku_file_history.log"
        self._max_log_entries = 10

        # UI初期化
        self._setup_ui()
        self._create_menu()
        self._connect_signals()
        self._setup_notification()

    def _setup_ui(self) -> None:
        """UIをセットアップする"""
        self.setWindowTitle("OYUWAKU - Untitled")
        self.setGeometry(100, 100, 1400, 800)

        # アイコンを設定
        icon_path = "icon.png"
        if Path(icon_path).exists():
            self.setWindowIcon(QIcon(icon_path))

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # レイアウト
        layout = QHBoxLayout(central_widget)

        # スプリッター（2ペイン）
        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        # スプリッターのスタイルを設定（境界線を見やすく）
        self._splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #d0d0d0;
                width: 4px;
            }
            QSplitter::handle:hover {
                background-color: #50a0f0;
            }
        """)

        # スプリッターをライブ更新に設定（ドラッグ中も更新）
        self._splitter.setOpaqueResize(True)

        # スプリッターのハンドル幅を設定
        self._splitter.setHandleWidth(4)

        # 左ペイン: Markdownエディタ
        self._editor = MarkdownEditor()
        self._splitter.addWidget(self._editor)

        # 右ペイン: マインドマップビュー
        self._mindmap_view = MindMapView(
            font_size=self._font_size,
            font_color=self._font_color,
            line_color=self._line_color,
            layout_direction=self._layout_direction
        )
        self._splitter.addWidget(self._mindmap_view)

        # 保存されたスプリッターサイズを復元、なければデフォルト（1:1）
        saved_sizes = self._settings.value("splitter_sizes", [700, 700], type=list)
        if saved_sizes and len(saved_sizes) == 2:
            self._splitter.setSizes(saved_sizes)
        else:
            self._splitter.setSizes([700, 700])

        # スプリッターサイズ変更時に保存
        self._splitter.splitterMoved.connect(self._on_splitter_moved)

        layout.addWidget(self._splitter)

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

        # 最近開いたファイル
        self._recent_files_menu = file_menu.addMenu("最近開いたファイル(&R)")
        self._update_recent_files_menu()

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

        # PNG形式でエクスポート
        export_png_action = QAction("PNG形式でエクスポート(&E)...", self)
        export_png_action.triggered.connect(self._on_export_png)
        file_menu.addAction(export_png_action)

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

        # マインドマップのノードがクリックされたときにエディタのカーソルを移動
        self._mindmap_view.node_clicked.connect(self._on_node_clicked)

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

        # 未保存の変更があることを記録
        self._has_unsaved_changes = True

        # 自動保存タイマーをリセット
        self._reset_autosave_timer()

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

    def _on_node_clicked(self, node: Node) -> None:
        """
        マインドマップのノードがクリックされたときの処理

        Args:
            node: クリックされたノード
        """
        # ノードから行番号を取得
        line_number = self._parser.get_line_by_node(node)
        if line_number is not None:
            # エディタのカーソルを移動
            self._editor.move_cursor_to_line(line_number)

    def _on_new(self) -> None:
        """新規作成"""
        # 未保存の変更があれば確認
        if not self._check_unsaved_changes():
            return

        self._editor.set_text("")
        self._mindmap.clear()
        self._current_file = None
        self._has_unsaved_changes = False
        self.setWindowTitle("OYUWAKU - Untitled")
        # 自動保存タイマーを停止（新規作成時は自動保存しない）
        self._autosave_timer.stop()

    def _on_open(self) -> None:
        """ファイルを開く"""
        # 未保存の変更があれば確認
        if not self._check_unsaved_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "ファイルを開く",
            "",
            "Markdown Files (*.md);;All Files (*)"
        )

        if file_path:
            self._open_file(file_path)

    def _open_file(self, file_path: str) -> None:
        """
        指定されたファイルを開く

        Args:
            file_path: 開くファイルのパス
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                markdown_text = f.read()
                self._editor.set_text(markdown_text)
                self._current_file = Path(file_path)
                self._has_unsaved_changes = False
                self.setWindowTitle(f"OYUWAKU - {self._current_file.name}")
                # 最近開いたファイルリストに追加
                self._add_recent_file(file_path)
                # ログに記録
                self._log_file_action("開く", file_path)
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
            self.setWindowTitle(f"OYUWAKU - {self._current_file.name}")

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
            # 未保存フラグをクリア
            self._has_unsaved_changes = False
            # ログに記録
            self._log_file_action("保存", str(file_path))
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"保存できませんでした:\n{e}")

    def _on_export_png(self) -> None:
        """PNG形式でエクスポート"""
        # ファイル保存ダイアログを表示
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "PNG形式でエクスポート",
            "mindmap.png",
            "PNG Files (*.png);;All Files (*)"
        )

        if file_path:
            # 拡張子がない場合は.pngを追加
            file_path_obj = Path(file_path)
            if not file_path_obj.suffix:
                file_path_obj = file_path_obj.with_suffix('.png')

            # マインドマップビューからPNGをエクスポート
            success = self._mindmap_view.export_to_png(str(file_path_obj))

            if success:
                QMessageBox.information(
                    self,
                    "エクスポート完了",
                    f"マインドマップをPNG形式で保存しました:\n{file_path_obj}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "エラー",
                    "PNG形式でのエクスポートに失敗しました"
                )

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

        # ペイン配置の読み込み（デフォルトは左右）
        self._pane_orientation = self._settings.value("pane_orientation", 0, type=int)

        # 最近開いたファイルの読み込み（テキストファイルから）
        self._load_recent_files()

    def _save_settings(self) -> None:
        """設定を保存する"""
        self._settings.setValue("font_size", self._font_size)
        self._settings.setValue("font_color", self._font_color.name())
        self._settings.setValue("line_color", self._line_color.name())
        self._settings.setValue("layout_direction", self._layout_direction)
        self._settings.setValue("pane_orientation", self._pane_orientation)

    def _on_settings(self) -> None:
        """設定ダイアログを開く"""
        dialog = SettingsDialog(self)
        dialog.set_font_size(self._font_size)
        dialog.set_font_color(self._font_color)
        dialog.set_line_color(self._line_color)
        dialog.set_layout_direction(self._layout_direction)
        dialog.set_pane_orientation(self._pane_orientation)

        # 適用ボタンが押されたときに設定を適用
        dialog.settings_changed.connect(lambda: self._apply_settings_from_dialog(dialog))

        if dialog.exec():
            # OKボタンが押されたときも設定を適用
            self._apply_settings_from_dialog(dialog)

    def _apply_settings_from_dialog(self, dialog: SettingsDialog) -> None:
        """
        設定ダイアログから設定を適用する

        Args:
            dialog: 設定ダイアログ
        """
        # 設定を取得
        new_font_size = dialog.get_font_size()
        new_font_color = dialog.get_font_color()
        new_line_color = dialog.get_line_color()
        new_layout_direction = dialog.get_layout_direction()
        new_pane_orientation = dialog.get_pane_orientation()
        apply_scope = dialog.get_apply_scope()

        # 適用範囲に応じて設定を適用
        selected_node = self._mindmap_view.get_selected_node()

        if apply_scope == 0:
            # 全体に適用
            self._font_size = new_font_size
            self._font_color = new_font_color
            self._line_color = new_line_color
            self._layout_direction = new_layout_direction

            # ペイン配置が変更された場合
            if self._pane_orientation != new_pane_orientation:
                self._pane_orientation = new_pane_orientation
                self._update_pane_orientation()

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

    def _reset_autosave_timer(self) -> None:
        """
        自動保存タイマーをリセットする

        テキストが変更されるたびに呼ばれ、最後の編集から5秒後に自動保存される
        """
        # 既存のファイルを開いている場合のみタイマーを開始
        if self._current_file is not None:
            self._autosave_timer.stop()
            self._autosave_timer.start()

    def _auto_save(self) -> None:
        """
        自動保存を実行する

        既存のファイルを開いている場合のみ保存される
        """
        # 既存のファイルを開いている場合のみ自動保存
        if self._current_file is not None:
            self._save_to_file(self._current_file)
            # 通知を表示
            self._show_notification("自動保存しました")

    def _setup_notification(self) -> None:
        """通知ラベルをセットアップする"""
        # 通知ラベルを作成
        self._notification_label = QLabel(self)
        self._notification_label.setStyleSheet("""
            QLabel {
                background-color: rgba(50, 150, 250, 220);
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        self._notification_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._notification_label.hide()

        # フェードアウト用のタイマー
        self._notification_timer = QTimer(self)
        self._notification_timer.setSingleShot(True)
        self._notification_timer.timeout.connect(self._hide_notification)

    def _show_notification(self, message: str) -> None:
        """
        通知を表示する

        Args:
            message: 表示するメッセージ
        """
        # メッセージを設定
        self._notification_label.setText(message)
        self._notification_label.adjustSize()

        # 右下に配置
        window_width = self.width()
        window_height = self.height()
        label_width = self._notification_label.width()
        label_height = self._notification_label.height()

        x = window_width - label_width - 30
        y = window_height - label_height - 50

        self._notification_label.move(x, y)
        self._notification_label.show()
        self._notification_label.raise_()

        # 2.5秒後に非表示にする
        self._notification_timer.start(2500)

    def _hide_notification(self) -> None:
        """通知を非表示にする"""
        self._notification_label.hide()

    def resizeEvent(self, event) -> None:
        """
        ウィンドウのリサイズイベント

        Args:
            event: リサイズイベント
        """
        super().resizeEvent(event)

        # 通知が表示されている場合は位置を更新
        if self._notification_label.isVisible():
            window_width = self.width()
            window_height = self.height()
            label_width = self._notification_label.width()
            label_height = self._notification_label.height()

            x = window_width - label_width - 30
            y = window_height - label_height - 50

            self._notification_label.move(x, y)

    def _add_recent_file(self, file_path: str) -> None:
        """
        最近開いたファイルリストに追加する

        Args:
            file_path: ファイルパス
        """
        # すでにリストに存在する場合は削除（重複を避けるため）
        if file_path in self._recent_files:
            self._recent_files.remove(file_path)

        # リストの先頭に追加
        self._recent_files.insert(0, file_path)

        # 最大数を超えた場合は古いものを削除
        if len(self._recent_files) > self._max_recent_files:
            self._recent_files = self._recent_files[:self._max_recent_files]

        # テキストファイルに保存
        self._save_recent_files()

        # メニューを更新
        self._update_recent_files_menu()

    def _update_recent_files_menu(self) -> None:
        """最近開いたファイルメニューを更新する"""
        # 既存のアクションをクリア
        self._recent_files_menu.clear()

        # ファイルが存在しない場合
        if not self._recent_files:
            no_files_action = QAction("（なし）", self)
            no_files_action.setEnabled(False)
            self._recent_files_menu.addAction(no_files_action)
            return

        # 各ファイルのアクションを追加
        for file_path in self._recent_files:
            # ファイルが実際に存在するか確認
            if Path(file_path).exists():
                # ファイル名のみを表示（フルパスではなく）
                file_name = Path(file_path).name
                action = QAction(file_name, self)
                action.setToolTip(file_path)  # ツールチップにフルパスを表示
                # ラムダ関数で現在のfile_pathを保持
                action.triggered.connect(lambda checked, fp=file_path: self._open_recent_file(fp))
                self._recent_files_menu.addAction(action)

    def _open_recent_file(self, file_path: str) -> None:
        """
        最近開いたファイルを開く

        Args:
            file_path: 開くファイルのパス
        """
        # 未保存の変更があれば確認
        if not self._check_unsaved_changes():
            return

        if Path(file_path).exists():
            self._open_file(file_path)
        else:
            QMessageBox.warning(
                self,
                "警告",
                f"ファイルが見つかりません:\n{file_path}\n\n最近開いたファイルリストから削除されます。"
            )
            # リストから削除
            if file_path in self._recent_files:
                self._recent_files.remove(file_path)
                self._save_recent_files()
                self._update_recent_files_menu()

    def _log_file_action(self, action: str, file_path: str) -> None:
        """
        ファイル操作をログに記録する

        Args:
            action: アクション（"開く" または "保存"）
            file_path: ファイルパス
        """
        try:
            # 現在のタイムスタンプ
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # ログエントリを作成
            log_entry = f"[{timestamp}] {action}: {file_path}\n"

            # 既存のログを読み込む
            if self._log_file_path.exists():
                with open(self._log_file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            else:
                lines = []

            # 新しいエントリを追加
            lines.append(log_entry)

            # 最大件数を超えた場合は古いものを削除
            if len(lines) > self._max_log_entries:
                lines = lines[-self._max_log_entries:]

            # ログファイルに書き込む
            with open(self._log_file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        except Exception as e:
            # ログ記録に失敗してもアプリケーションの動作には影響しないようにする
            print(f"ログ記録エラー: {e}")

    def _check_unsaved_changes(self) -> bool:
        """
        未保存の変更があるかチェックし、ある場合は保存確認ダイアログを表示

        Returns:
            True=処理を続行、False=キャンセル
        """
        if not self._has_unsaved_changes:
            return True

        # 保存確認ダイアログを表示
        reply = QMessageBox.question(
            self,
            "未保存の変更",
            "変更が保存されていません。保存しますか？",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )

        if reply == QMessageBox.StandardButton.Save:
            # 保存を実行
            if self._current_file:
                self._save_to_file(self._current_file)
                return True
            else:
                # 新規ファイルの場合は「名前を付けて保存」
                self._on_save_as()
                # 保存がキャンセルされた場合は current_file が None のまま
                return self._current_file is not None
        elif reply == QMessageBox.StandardButton.Discard:
            # 保存せずに続行
            return True
        else:
            # キャンセル
            return False

    def closeEvent(self, event) -> None:
        """
        アプリケーションを閉じるときのイベント

        Args:
            event: クローズイベント
        """
        # 未保存の変更をチェック
        if self._check_unsaved_changes():
            event.accept()
        else:
            event.ignore()

    def _on_splitter_moved(self, pos: int, index: int) -> None:
        """
        スプリッターが移動したときの処理

        Args:
            pos: 移動後の位置
            index: スプリッターのインデックス
        """
        # 現在のサイズを保存
        sizes = self._splitter.sizes()
        self._settings.setValue("splitter_sizes", sizes)

    def _update_pane_orientation(self) -> None:
        """ペイン配置を更新する"""
        # 現在のスプリッターのサイズを保存
        current_sizes = self._splitter.sizes()

        # スプリッターの向きを設定
        if self._pane_orientation == 0:
            # 左右配置
            self._splitter.setOrientation(Qt.Orientation.Horizontal)
        else:
            # 上下配置
            self._splitter.setOrientation(Qt.Orientation.Vertical)

        # サイズを復元（向きが変わっても比率を保つ）
        self._splitter.setSizes(current_sizes)

    def _load_recent_files(self) -> None:
        """最近開いたファイルのリストをテキストファイルから読み込む"""
        try:
            if self._recent_files_path.exists():
                with open(self._recent_files_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 各行から改行を除去してリストに追加
                    self._recent_files = [line.strip() for line in lines if line.strip()]
                    # 最大数を超えている場合は切り詰める
                    if len(self._recent_files) > self._max_recent_files:
                        self._recent_files = self._recent_files[:self._max_recent_files]
        except Exception as e:
            # 読み込みエラーが発生してもアプリケーションは続行
            print(f"最近開いたファイルの読み込みエラー: {e}")
            self._recent_files = []

    def _save_recent_files(self) -> None:
        """最近開いたファイルのリストをテキストファイルに保存する"""
        try:
            with open(self._recent_files_path, 'w', encoding='utf-8') as f:
                for file_path in self._recent_files:
                    f.write(f"{file_path}\n")
        except Exception as e:
            # 保存エラーが発生してもアプリケーションは続行
            print(f"最近開いたファイルの保存エラー: {e}")

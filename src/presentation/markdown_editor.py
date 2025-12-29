"""
Markdownエディタウィジェット

左ペインのMarkdown編集エリア
"""
from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtCore import pyqtSignal


class MarkdownEditor(QPlainTextEdit):
    """Markdownテキストエディタ"""

    # テキスト変更時のシグナル
    text_changed = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        """
        エディタを初期化する

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """UIをセットアップする"""
        # フォント設定
        font = self.font()
        font.setFamily("Monaco")
        font.setPointSize(12)
        self.setFont(font)

        # プレースホルダーテキスト
        self.setPlaceholderText("Markdownリスト形式または見出し形式で入力してください...\n\n例（リスト）:\n- プロジェクト計画\n  - フェーズ1\n    - タスク1\n\n例（見出し）:\n# ルート\n## 子ノード")

    def _connect_signals(self) -> None:
        """シグナルを接続する"""
        # テキスト変更時に独自シグナルを発火
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self) -> None:
        """テキスト変更時の処理"""
        self.text_changed.emit(self.toPlainText())

    def get_text(self) -> str:
        """
        エディタのテキストを取得する

        Returns:
            エディタ内のテキスト
        """
        return self.toPlainText()

    def set_text(self, text: str) -> None:
        """
        エディタのテキストを設定する

        Args:
            text: 設定するテキスト
        """
        self.setPlainText(text)

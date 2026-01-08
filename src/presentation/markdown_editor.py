"""
Markdownエディタウィジェット

左ペインのMarkdown編集エリア
"""
import re
from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QKeyEvent, QTextCursor


class MarkdownEditor(QPlainTextEdit):
    """Markdownテキストエディタ"""

    # テキスト変更時のシグナル
    text_changed = pyqtSignal(str)
    # カーソル位置変更時のシグナル（行番号を送信）
    cursor_line_changed = pyqtSignal(int)

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
        # カーソル位置変更時にシグナルを発火
        self.cursorPositionChanged.connect(self._on_cursor_position_changed)

    def _on_text_changed(self) -> None:
        """テキスト変更時の処理"""
        self.text_changed.emit(self.toPlainText())

    def _on_cursor_position_changed(self) -> None:
        """カーソル位置変更時の処理"""
        cursor = self.textCursor()
        line_number = cursor.blockNumber()  # 0始まりの行番号
        self.cursor_line_changed.emit(line_number)

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

    def move_cursor_to_line(self, line_number: int) -> None:
        """
        カーソルを指定行のテキスト先頭に移動する

        Args:
            line_number: 移動先の行番号（0始まり）
        """
        # QTextCursorを取得
        cursor = self.textCursor()

        # ドキュメントの先頭に移動
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        # 指定行まで移動
        for _ in range(line_number):
            cursor.movePosition(QTextCursor.MoveOperation.Down)

        # 行の先頭に移動
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)

        # 行のテキストを取得
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        line_text = cursor.selectedText()

        # 選択を解除して行の先頭に戻る
        cursor.clearSelection()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)

        # リストパターン: インデント + "- " または "* " + テキスト
        list_pattern = re.match(r'^(\s*)([-*])\s+', line_text)
        if list_pattern:
            # リストマーカーの後にカーソルを移動
            indent = list_pattern.group(1)  # インデント部分
            marker = list_pattern.group(2)  # - または *
            prefix_length = len(indent) + len(marker) + 1  # "  - " の長さ（スペース含む）
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, prefix_length)
        else:
            # 見出しパターン: "# " + テキスト
            heading_pattern = re.match(r'^(#{1,6})\s+', line_text)
            if heading_pattern:
                # 見出しマーカーの後にカーソルを移動
                prefix_length = len(heading_pattern.group(0))
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, prefix_length)

        # カーソルを設定
        self.setTextCursor(cursor)

        # カーソル位置を画面中央に表示
        self.centerCursor()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        キー押下イベントを処理する

        Args:
            event: キーイベント
        """
        # Enterキー: 自動リスト継続
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._handle_enter_key():
                event.accept()
                return

        # Tabキー: インデント追加（スペース2つ）
        if event.key() == Qt.Key.Key_Tab:
            cursor = self.textCursor()

            # 複数行選択されている場合
            if cursor.hasSelection():
                self._indent_selected_lines(cursor, indent=True)
            else:
                # 単一行の場合: 行頭にスペース2つを挿入
                original_position = cursor.position()
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                line_start = cursor.position()
                cursor.insertText("  ")
                # カーソル位置を調整（2文字分右にシフト）
                cursor.setPosition(original_position + 2)
                self.setTextCursor(cursor)

            event.accept()
            return

        # Shift+Tab: インデント削除
        if event.key() == Qt.Key.Key_Backtab:
            cursor = self.textCursor()

            # 複数行選択されている場合
            if cursor.hasSelection():
                self._indent_selected_lines(cursor, indent=False)
            else:
                # 単一行の場合: 行頭のスペース2つを削除
                original_position = cursor.position()
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                line_start = cursor.position()
                cursor.movePosition(QTextCursor.MoveOperation.Right,
                                  QTextCursor.MoveMode.KeepAnchor, 2)
                selected_text = cursor.selectedText()

                # スペース2つの場合のみ削除
                if selected_text == "  ":
                    cursor.removeSelectedText()
                    # カーソル位置を調整（削除した分左にシフト、ただし行頭より前には行かない）
                    new_position = max(line_start, original_position - 2)
                    cursor.setPosition(new_position)
                else:
                    # スペース2つでない場合は元の位置に戻す
                    cursor.setPosition(original_position)

                self.setTextCursor(cursor)

            event.accept()
            return

        # その他のキーは通常処理
        super().keyPressEvent(event)

    def _handle_enter_key(self) -> bool:
        """
        Enterキー押下時の処理（自動リスト継続）

        Returns:
            True=処理した、False=通常のEnter処理を継続
        """
        cursor = self.textCursor()
        original_position = cursor.position()

        # 現在の行のテキストと行の開始位置を取得
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        line_start = cursor.position()
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        current_line = cursor.selectedText()

        # カーソルを元の位置に戻す
        cursor.setPosition(original_position)

        # リストパターン: インデント + "- " または "* "
        list_pattern = re.match(r'^(\s*)([-*])\s+(.*)$', current_line)

        if list_pattern:
            indent = list_pattern.group(1)  # インデント部分
            marker = list_pattern.group(2)  # - または *
            content = list_pattern.group(3)  # リスト項目の内容

            # カーソル位置が行内のどこにあるかを計算
            cursor_offset = original_position - line_start
            prefix_length = len(indent) + len(marker) + 1  # "  - " の長さ

            # カーソルがリストマーカー部分にある場合
            if cursor_offset <= prefix_length:
                # カーソル位置以前のテキストは保持、以降は新しい行へ
                text_after_cursor = current_line[cursor_offset:]

                # 現在の行のカーソル位置以降を削除
                cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()

                # 改行して新しいリスト項目を追加
                cursor.insertText(f"\n{text_after_cursor}")
                self.setTextCursor(cursor)
                return True

            # カーソルがコンテンツ部分にある場合
            # カーソル位置以降のテキストを取得
            text_before_cursor = current_line[:cursor_offset]
            text_after_cursor = current_line[cursor_offset:]

            # 空のリスト項目の場合（"- "のみ）はリストを終了
            if not content.strip():
                # 現在の行の"- "を削除して改行
                cursor.select(QTextCursor.SelectionType.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.insertText("\n")
                return True

            # カーソル位置以降にテキストがある場合、それを新しい行に移動
            if text_after_cursor:
                # 現在の行のカーソル位置以降を削除
                cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()

                # 改行して新しいリスト項目を追加し、カーソル以降のテキストを挿入
                cursor.insertText(f"\n{indent}{marker} {text_after_cursor}")
                self.setTextCursor(cursor)
                return True
            else:
                # カーソル位置以降にテキストがない場合は通常のリスト継続
                cursor.insertText(f"\n{indent}{marker} ")
                self.setTextCursor(cursor)
                return True

        # リスト項目でない場合は通常のEnter処理
        return False

    def _indent_selected_lines(self, cursor: QTextCursor, indent: bool) -> None:
        """
        選択された行のインデントを追加/削除する

        Args:
            cursor: テキストカーソル
            indent: True=インデント追加、False=インデント削除
        """
        # 選択範囲の開始・終了位置を取得
        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        # カーソルを選択開始位置に移動
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)

        # 編集操作を一つのアンドゥ単位にまとめる
        cursor.beginEditBlock()

        # 選択範囲の各行を処理
        while cursor.position() <= end:
            if indent:
                # インデント追加: 行頭にスペース2つを挿入
                cursor.insertText("  ")
                end += 2  # 挿入した分、終了位置を調整
            else:
                # インデント削除: 行頭のスペース2つを削除
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                cursor.movePosition(QTextCursor.MoveOperation.Right,
                                  QTextCursor.MoveMode.KeepAnchor, 2)
                selected_text = cursor.selectedText()

                # スペース2つの場合のみ削除
                if selected_text == "  ":
                    cursor.removeSelectedText()
                    end -= 2  # 削除した分、終了位置を調整
                else:
                    # スペース2つでない場合はカーソルを行末に移動
                    cursor.clearSelection()

            # 次の行に移動
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
            if not cursor.movePosition(QTextCursor.MoveOperation.Down):
                break
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)

        cursor.endEditBlock()
        self.setTextCursor(cursor)

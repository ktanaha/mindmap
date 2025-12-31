"""
設定ダイアログ

フォントサイズと色を設定するダイアログ
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QColorDialog, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


class SettingsDialog(QDialog):
    """設定ダイアログクラス"""

    # 設定が変更されたときのシグナル
    settings_changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        """
        設定ダイアログを初期化する

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.setModal(True)
        self.resize(400, 300)

        # 現在の設定値
        self._font_size = 14
        self._font_color = QColor(0, 0, 0)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIをセットアップする"""
        layout = QVBoxLayout(self)

        # フォントサイズグループ
        font_group = QGroupBox("フォント設定")
        font_layout = QVBoxLayout()

        # フォントサイズ
        size_layout = QHBoxLayout()
        size_label = QLabel("フォントサイズ:")
        self._size_spinbox = QSpinBox()
        self._size_spinbox.setRange(8, 72)
        self._size_spinbox.setValue(self._font_size)
        self._size_spinbox.setSuffix(" pt")
        size_layout.addWidget(size_label)
        size_layout.addWidget(self._size_spinbox)
        size_layout.addStretch()
        font_layout.addLayout(size_layout)

        # フォント色
        color_layout = QHBoxLayout()
        color_label = QLabel("フォント色:")
        self._color_button = QPushButton()
        self._color_button.setFixedSize(100, 30)
        self._update_color_button()
        self._color_button.clicked.connect(self._choose_color)
        color_layout.addWidget(color_label)
        color_layout.addWidget(self._color_button)
        color_layout.addStretch()
        font_layout.addLayout(color_layout)

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        layout.addStretch()

        # ボタン
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def _choose_color(self) -> None:
        """色選択ダイアログを表示する"""
        color = QColorDialog.getColor(self._font_color, self, "フォント色を選択")
        if color.isValid():
            self._font_color = color
            self._update_color_button()

    def _update_color_button(self) -> None:
        """カラーボタンの表示を更新する"""
        self._color_button.setStyleSheet(
            f"background-color: {self._font_color.name()};"
        )

    def set_font_size(self, size: int) -> None:
        """
        フォントサイズを設定する

        Args:
            size: フォントサイズ
        """
        self._font_size = size
        self._size_spinbox.setValue(size)

    def set_font_color(self, color: QColor) -> None:
        """
        フォント色を設定する

        Args:
            color: フォント色
        """
        self._font_color = color
        self._update_color_button()

    def get_font_size(self) -> int:
        """
        フォントサイズを取得する

        Returns:
            フォントサイズ
        """
        return self._size_spinbox.value()

    def get_font_color(self) -> QColor:
        """
        フォント色を取得する

        Returns:
            フォント色
        """
        return self._font_color

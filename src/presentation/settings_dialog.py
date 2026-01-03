"""
設定ダイアログ

フォントサイズと色を設定するダイアログ
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QColorDialog, QGroupBox, QRadioButton, QButtonGroup
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
        self.resize(450, 450)

        # 現在の設定値
        self._font_size = 14
        self._font_color = QColor(0, 0, 0)
        self._line_color = QColor(150, 150, 150)
        self._layout_direction = 0  # 0: 右のみ, 1: 左右交互

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

        # 線の設定グループ
        line_group = QGroupBox("線の設定")
        line_layout = QVBoxLayout()

        # 線の色
        line_color_layout = QHBoxLayout()
        line_color_label = QLabel("線の色:")
        self._line_color_button = QPushButton()
        self._line_color_button.setFixedSize(100, 30)
        self._update_line_color_button()
        self._line_color_button.clicked.connect(self._choose_line_color)
        line_color_layout.addWidget(line_color_label)
        line_color_layout.addWidget(self._line_color_button)
        line_color_layout.addStretch()
        line_layout.addLayout(line_color_layout)

        line_group.setLayout(line_layout)
        layout.addWidget(line_group)

        # ペイン配置設定グループ
        pane_orientation_group = QGroupBox("ペイン配置")
        pane_orientation_layout = QVBoxLayout()

        self._pane_orientation_button_group = QButtonGroup()
        self._pane_horizontal = QRadioButton("左右に配置（エディタ | マインドマップ）")
        self._pane_vertical = QRadioButton("上下に配置（エディタ上、マインドマップ下）")

        self._pane_orientation_button_group.addButton(self._pane_horizontal, 0)
        self._pane_orientation_button_group.addButton(self._pane_vertical, 1)
        self._pane_horizontal.setChecked(True)  # デフォルトは左右

        pane_orientation_layout.addWidget(self._pane_horizontal)
        pane_orientation_layout.addWidget(self._pane_vertical)

        pane_orientation_group.setLayout(pane_orientation_layout)
        layout.addWidget(pane_orientation_group)

        # レイアウト設定グループ（マインドマップのノード配置）
        layout_group = QGroupBox("マインドマップノード配置")
        layout_layout = QVBoxLayout()

        self._layout_button_group = QButtonGroup()
        self._layout_right_only = QRadioButton("右側のみに展開")
        self._layout_alternate = QRadioButton("左右交互に展開")
        self._layout_down_only = QRadioButton("下側のみに展開")
        self._layout_vertical_alternate = QRadioButton("上下交互に展開")

        self._layout_button_group.addButton(self._layout_right_only, 0)
        self._layout_button_group.addButton(self._layout_alternate, 1)
        self._layout_button_group.addButton(self._layout_down_only, 2)
        self._layout_button_group.addButton(self._layout_vertical_alternate, 3)
        self._layout_right_only.setChecked(True)  # デフォルトは右のみ

        layout_layout.addWidget(self._layout_right_only)
        layout_layout.addWidget(self._layout_alternate)
        layout_layout.addWidget(self._layout_down_only)
        layout_layout.addWidget(self._layout_vertical_alternate)

        layout_group.setLayout(layout_layout)
        layout.addWidget(layout_group)

        # 適用範囲グループ
        scope_group = QGroupBox("適用範囲")
        scope_layout = QVBoxLayout()

        self._scope_button_group = QButtonGroup()
        self._scope_all = QRadioButton("全体に適用")
        self._scope_selected = QRadioButton("選択中のノードのみ")
        self._scope_subtree = QRadioButton("選択中のノード以下すべて")

        self._scope_button_group.addButton(self._scope_all, 0)
        self._scope_button_group.addButton(self._scope_selected, 1)
        self._scope_button_group.addButton(self._scope_subtree, 2)
        self._scope_all.setChecked(True)  # デフォルトは全体

        scope_layout.addWidget(self._scope_all)
        scope_layout.addWidget(self._scope_selected)
        scope_layout.addWidget(self._scope_subtree)

        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)

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

    def _choose_line_color(self) -> None:
        """線の色選択ダイアログを表示する"""
        color = QColorDialog.getColor(self._line_color, self, "線の色を選択")
        if color.isValid():
            self._line_color = color
            self._update_line_color_button()

    def _update_line_color_button(self) -> None:
        """線の色ボタンの表示を更新する"""
        self._line_color_button.setStyleSheet(
            f"background-color: {self._line_color.name()};"
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

    def set_line_color(self, color: QColor) -> None:
        """
        線の色を設定する

        Args:
            color: 線の色
        """
        self._line_color = color
        self._update_line_color_button()

    def get_line_color(self) -> QColor:
        """
        線の色を取得する

        Returns:
            線の色
        """
        return self._line_color

    def get_apply_scope(self) -> int:
        """
        適用範囲を取得する

        Returns:
            0: 全体、1: 選択ノードのみ、2: 選択ノード以下
        """
        return self._scope_button_group.checkedId()

    def set_layout_direction(self, direction: int) -> None:
        """
        レイアウト方向を設定する

        Args:
            direction: 0=右のみ, 1=左右交互, 2=下のみ, 3=上下交互
        """
        self._layout_direction = direction
        if direction == 0:
            self._layout_right_only.setChecked(True)
        elif direction == 1:
            self._layout_alternate.setChecked(True)
        elif direction == 2:
            self._layout_down_only.setChecked(True)
        else:
            self._layout_vertical_alternate.setChecked(True)

    def get_layout_direction(self) -> int:
        """
        レイアウト方向を取得する

        Returns:
            0: 右のみ、1: 左右交互、2: 下のみ、3: 上下交互
        """
        return self._layout_button_group.checkedId()

    def set_pane_orientation(self, orientation: int) -> None:
        """
        ペイン配置を設定する

        Args:
            orientation: 0=左右、1=上下
        """
        if orientation == 0:
            self._pane_horizontal.setChecked(True)
        else:
            self._pane_vertical.setChecked(True)

    def get_pane_orientation(self) -> int:
        """
        ペイン配置を取得する

        Returns:
            0: 左右、1: 上下
        """
        return self._pane_orientation_button_group.checkedId()

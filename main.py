#!/usr/bin/env python3
"""
OYUWAKU Application

Markdown駆動型マインドマップアプリケーション
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.presentation.main_window import MainWindow


def main() -> int:
    """
    アプリケーションのエントリーポイント

    Returns:
        終了コード
    """
    # QApplicationの作成
    app = QApplication(sys.argv)
    app.setApplicationName("OYUWAKU")
    app.setOrganizationName("OYUWAKU")

    # メインウィンドウの作成と表示
    window = MainWindow()
    window.show()

    # イベントループの実行
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

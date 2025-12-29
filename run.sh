#!/bin/bash
# MindMapアプリケーション起動スクリプト

cd "$(dirname "$0")"

# 仮想環境をアクティベート
source venv/bin/activate

# アプリケーション起動
python main.py

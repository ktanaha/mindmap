#!/bin/bash
# Claude Code セッションログ記録補助スクリプト
# 使い方: ./log_session.sh "メッセージ内容"

LOG_FILE="claude.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# ログファイルが存在しない場合は作成
if [ ! -f "$LOG_FILE" ]; then
    echo "=== Claude Code セッションログ ===" > "$LOG_FILE"
    echo "" >> "$LOG_FILE"
fi

# メッセージをログに追記
if [ $# -eq 0 ]; then
    echo "[$TIMESTAMP] ログエントリが追加されました" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] $*" >> "$LOG_FILE"
fi

echo "ログを記録しました: $LOG_FILE"

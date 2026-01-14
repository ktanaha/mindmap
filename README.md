# MindMap - Markdown駆動型マインドマップアプリケーション

思考整理と学習メモのためのシンプルなマインドマップアプリケーション

## 特徴

- **2ペイン表示**: 左でMarkdown編集、右でマインドマップをリアルタイム表示
- **Markdown駆動**: 見出しレベルでノードの階層を自然に表現
- **直感的な操作**: ドラッグ&ドロップでノードの位置・親子関係を自由に変更
- **ローカルファースト**: データは全てローカルに保存（JSON形式）

## スクリーンショット

*開発中*

## 必須要件

- **OS**: macOS
- **Python**: 3.10以上

## インストール

### 1. リポジトリのクローン

```bash
cd /path/to/your/workspace
git clone <repository-url>
cd mindmap
```

### 2. 仮想環境のセットアップ

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. アプリケーションのインストール（推奨）

開発モードでインストールすると、`oyuwaku`コマンドで起動できるようになります。

```bash
pip install -e .
```

## 使い方

### アプリケーションの起動

**方法1: コマンドとして起動（推奨）**

インストール後は、どこからでも起動できます。

```bash
oyuwaku
```

**方法2: 起動スクリプトを使用**

```bash
./run.sh
```

**方法3: 直接起動**

```bash
source venv/bin/activate
python main.py
```

### 基本操作

#### Markdownエディタ（左ペイン）

Markdown形式でテキストを入力します。**リスト表記**または**見出し表記**が使えます。

**リスト表記（推奨）:**
```markdown
- プロジェクト計画
  - フェーズ1：設計
    - 要件定義
    - UI設計
  - フェーズ2：実装
    - バックエンド開発
    - フロントエンド開発
  - フェーズ3：テスト
```

**見出し表記:**
```markdown
# ルートノード
## 子ノード1
### 孫ノード1-1
### 孫ノード1-2
## 子ノード2
```

#### マインドマップビュー（右ペイン）

Markdownエディタで入力した内容がリアルタイムでマインドマップとして表示されます。

- 階層の深さに応じてノードの色が変わります
- ノード間の接続線が自動的に描画されます

### ファイル操作

- **新規作成**: メニュー > ファイル > 新規
- **開く**: メニュー > ファイル > 開く
- **保存**: メニュー > ファイル > 保存 (Cmd+S)
- **名前を付けて保存**: メニュー > ファイル > 名前を付けて保存

## 開発

### プロジェクト構成

```
mindmap/
├── main.py                 # エントリーポイント
├── run.sh                  # 起動スクリプト
├── src/
│   ├── presentation/      # UI層
│   │   ├── main_window.py
│   │   ├── markdown_editor.py
│   │   └── mindmap_view.py
│   ├── parser/            # Markdownパーサー層
│   │   └── markdown_parser.py
│   ├── domain/            # ドメイン層
│   │   ├── node.py
│   │   └── mindmap.py
│   └── storage/           # 永続化層（将来実装）
├── tests/                 # テストコード
│   ├── domain/           # ドメイン層テスト（100%カバレッジ）
│   └── parser/           # パーサー層テスト
├── requirements.txt       # Python依存パッケージ
└── README.md             # このファイル
```

### テストの実行

```bash
pytest
```

## ドキュメント

### ユーザー向けドキュメント
- [FEATURES.md](FEATURES.md) - 機能一覧
- [HELP.md](HELP.md) - ヘルプドキュメント

### 開発者向けドキュメント
- [REQUIREMENTS.md](REQUIREMENTS.md) - 要件定義書
- [docs/](docs/) - Claude開発ガイドライン
  - [CLAUDE.md](docs/CLAUDE.md) - 開発方針全般
  - [CLAUDE_TDD.md](docs/CLAUDE_TDD.md) - TDDとテスト戦略
  - [CLAUDE_GIT.md](docs/CLAUDE_GIT.md) - Git管理・バージョン管理
  - [CLAUDE_CICD.md](docs/CLAUDE_CICD.md) - CI/CD設定
  - [CLAUDE_SECURITY.md](docs/CLAUDE_SECURITY.md) - セキュリティ・安全性ルール
  - [CLAUDE_LOGGER.md](docs/CLAUDE_LOGGER.md) - vibe-coding-logger統合ガイド
  - [CLAUDE_BACKLOG.md](docs/CLAUDE_BACKLOG.md) - プロダクトバックログ管理

## 技術スタック

- **GUI**: PyQt6 / PySide6
- **Markdownパーサー**: markdown / mistune
- **データ保存**: JSON
- **テスト**: pytest, pytest-qt

## ロードマップ

- [x] 基本要件定義
- [x] アーキテクチャ設計
- [x] **MVP開発完了！**
  - [x] 2ペインUI実装
  - [x] Markdownエディタ実装
  - [x] マインドマップビュー実装
  - [x] Markdownパーサー実装
  - [x] ファイル保存/読み込み（JSON形式）
  - [x] リアルタイム同期機能
- [ ] 追加機能
  - [ ] ドラッグ&ドロップでノード移動
  - [ ] ノードのカスタマイズ（色、アイコン）
  - [ ] 検索機能
  - [ ] エクスポート機能（PNG、PDF）
  - [ ] マップの拡大/縮小

## ライセンス

*TBD*

## 貢献

*TBD*

---

開発開始日: 2025-12-27

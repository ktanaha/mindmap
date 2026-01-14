# Claude開発ガイドライン

このディレクトリには、Claude Codeを使った開発のためのガイドラインドキュメントが含まれています。

## ドキュメント一覧

### [CLAUDE.md](CLAUDE.md)
開発方針全般とアーキテクチャの基本方針を定義。プロジェクト初期化、API開発、リファクタリングなどの開発指示テンプレートも含む。

### [CLAUDE_TDD.md](CLAUDE_TDD.md)
TDDとテスト戦略に関するガイドライン。Red-Green-Refactorサイクル、テストカバレッジ、ユニットテスト、統合テスト、E2Eテストの方針を定義。

### [CLAUDE_GIT.md](CLAUDE_GIT.md)
Git管理とバージョン管理のベストプラクティス。ブランチ戦略、コミットメッセージ規約、タグ管理、マージ戦略などを定義。

### [CLAUDE_CICD.md](CLAUDE_CICD.md)
CI/CD設定とデプロイメント戦略。GitHub Actions、自動テスト、デプロイフロー、環境管理などを定義。

### [CLAUDE_SECURITY.md](CLAUDE_SECURITY.md)
セキュリティと安全性ルール。認証・認可、データ保護、入力検証、依存関係管理、セキュリティテストなどのセキュリティガイドライン。

### [CLAUDE_LOGGER.md](CLAUDE_LOGGER.md)
vibe-coding-logger統合ガイド。開発中のロギング機能の実装方法とベストプラクティス。

### [CLAUDE_BACKLOG.md](CLAUDE_BACKLOG.md)
プロダクトバックログ管理。ユーザーストーリー、タスク管理、優先順位付けなどの管理方法を定義。

## 使い方

1. **プロジェクト開始時**: [CLAUDE.md](CLAUDE.md)を読んで開発方針を理解
2. **テスト戦略**: [CLAUDE_TDD.md](CLAUDE_TDD.md)でTDDの進め方を確認
3. **Git管理**: [CLAUDE_GIT.md](CLAUDE_GIT.md)でブランチ戦略とコミット規約を確認
4. **セキュリティ**: [CLAUDE_SECURITY.md](CLAUDE_SECURITY.md)でセキュリティ要件を確認

## 注意事項

これらのドキュメントは、Claude Codeによる開発を支援するための内部ガイドラインです。プロジェクト固有の要件に応じて適宜カスタマイズしてください。

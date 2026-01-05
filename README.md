# Pinned Discord Bot

📌 リアクションでメッセージを簡単にピン留めできるDiscord Botです。

## 機能

- **リアクションでピン留め**: メッセージに 📌 絵文字を付けると自動的にピン留め
- **リアクション削除でピン解除**: 📌 リアクションを外すとピン留め解除（全ユーザーがリアクションを外した場合）
- **ピン留め一覧表示**: `/pinnedlist` スラッシュコマンドでピン留めメッセージを一覧表示
- **コマンド対応**: ヘルプ表示、動作テスト、ステータス確認

## スラッシュコマンド

| コマンド | 説明 |
|---------|------|
| `/pinnedlist` | 全員のピン留めメッセージ一覧を表示 |
| `/pinnedlist user:@ユーザー` | 指定ユーザーのピン留めメッセージを表示 |
| `/pinnedlist days:7` | 過去7日間のピン留めメッセージを表示 |

### まとめて解除機能

`/pinnedlist` を実行すると、ピン留めメッセージ一覧と解除用UIが表示されます。

**表示の区別:**
- 📌 自分だけがピン留めしているメッセージ（解除可能）
- 🔒 他の人もピン留めしているメッセージ（解除不可、投稿者名表示）

**操作:**
1. ドロップダウンから解除したいメッセージを選択（複数選択可能）
2. 「適用」ボタンで選択したメッセージのピン留めを一括解除
3. 「キャンセル」ボタンで操作を中止

**注意**: 自分だけがピン留めしているメッセージのみ解除可能です。最大25件まで選択できます。

### 出力例

```
📌 全員のピン留めメッセージ一覧

📌 [Discord Bo...](メッセージリンク)
📌 [新機能実装...](メッセージリンク)
🔒 [バグ報告:...](メッセージリンク) by shotafujie

合計 3 件 | 📌 自分: 2件（解除可能）

[▼ 解除するメッセージを選択...]
[適用] [キャンセル]
```

## テキストコマンド

| コマンド | 説明 |
|---------|------|
| `!pin help` または `!pinhelp` | 使い方を表示 |
| `!pin test` | Botの動作テスト |
| `!pin status` | Botの状態とピン留め数を表示 |

## セットアップ

### 1. Discord Botトークンの取得

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」で新しいアプリケーションを作成
3. 「Bot」セクションで「Add Bot」をクリック
4. トークンをコピー
5. 「Privileged Gateway Intents」で以下を有効化:
   - Message Content Intent
   - Server Members Intent（任意）

### 2. Botの招待

OAuth2 URL Generatorで以下の権限を付与:
- `bot` スコープ
- 権限: `Manage Messages`, `Read Message History`, `Send Messages`, `Add Reactions`

### 3. 環境変数の設定

`.env` ファイルを作成:

```env
DISCORD_TOKEN=your_bot_token_here
```

## 実行方法

### ローカル実行

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# Bot起動
python main.py
```

### Docker実行

```bash
# イメージのビルド
docker build -t pinned-discord-bot .

# コンテナ起動
docker run -e DISCORD_TOKEN=your_token_here pinned-discord-bot
```

## プロジェクト構成

```
PinnedDiscordBot/
├── main.py           # Discord Bot本体
├── server.py         # ヘルスチェック用FastAPIサーバー
├── views/
│   └── unpin_view.py # まとめて解除用UI（View/Select/Button）
├── tests/
│   ├── conftest.py   # テストフィクスチャ
│   └── test_unpin_view.py  # ユニットテスト
├── requirements.txt  # Python依存パッケージ
├── Dockerfile        # Docker設定
└── README.md         # このファイル
```

## 依存パッケージ

- `discord.py==2.6.4` - Discord API
- `python-dotenv==1.0.1` - 環境変数読み込み
- `fastapi==0.110.1` - ヘルスチェックサーバー
- `uvicorn==0.29.0` - ASGIサーバー
- `pytest==8.3.4` - テストフレームワーク（開発用）
- `pytest-asyncio==0.24.0` - 非同期テストサポート（開発用）

## ヘルスチェックエンドポイント

デプロイ環境（Koyeb等）向けにHTTPエンドポイントを提供:

| エンドポイント | 説明 |
|---------------|------|
| `GET /` | ルートパス |
| `GET /health` | ヘルスチェック |
| `GET /status` | ステータス確認 |

ポート: `8080`

## 注意事項

- 1チャンネルあたり最大50件までピン留め可能（Discord制限）
- Botには「メッセージの管理」権限が必要
- Bot自身のリアクションは無視されます

## 変更履歴

### 2026-01-05
- **新機能**: まとめてピン留め解除機能を追加
  - `/pinnedlist` コマンドにSelect Menu（複数選択）と適用/キャンセルボタンを追加
  - 自分のピン留めメッセージを選択して一括解除可能
  - 最大25件まで選択可能（Discord制限）
- **変更**: `discord.py` を 2.3.2 から 2.6.4 にアップグレード（Python 3.13対応）
- **追加**: pytest によるユニットテスト基盤を整備

### 2025-12-20
- **新機能**: `/pinnedlist` スラッシュコマンドを追加
  - 自分のピン留めメッセージ一覧を表示
  - 期間フィルタリング機能（過去N日間）
  - Embed形式での見やすい表示
  - メッセージリンク埋め込み
- **変更**: `discord.Client` から `discord.ext.commands.Bot` に移行（スラッシュコマンド対応）

### 2025-12-06
- **修正**: リアクション削除イベントが発火しない問題を根本的に解決
  - **問題**: Bot起動前やキャッシュから消えたメッセージに対するリアクション削除イベントが発火せず、ピン留めが解除されなかった
  - **原因**: `on_reaction_add`/`on_reaction_remove`はメッセージがキャッシュにある場合のみ動作する
  - **対策**: キャッシュ不要な`on_raw_reaction_add`/`on_raw_reaction_remove`に全面移行
  - **効果**: Bot起動前のメッセージや古いメッセージでもリアクションの追加・削除が正しく処理されるようになりました

## ライセンス

MIT License

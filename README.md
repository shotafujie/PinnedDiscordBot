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
| `/pinnedlist` | 自分のピン留めメッセージ一覧を表示 |
| `/pinnedlist user:@ユーザー` | 指定ユーザーのピン留めメッセージを表示 |
| `/pinnedlist days:7` | 過去7日間のピン留めメッセージを表示 |

### 出力例

```
📌 shotafujie さんのピン留めメッセージ一覧

• [Discord Bo...](メッセージリンク)
• [新機能実装...](メッセージリンク)
• [バグ報告:...](メッセージリンク)

合計 3 件
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
├── requirements.txt  # Python依存パッケージ
├── Dockerfile        # Docker設定
└── README.md         # このファイル
```

## 依存パッケージ

- `discord.py==2.3.2` - Discord API
- `python-dotenv==1.0.1` - 環境変数読み込み
- `fastapi==0.110.1` - ヘルスチェックサーバー
- `uvicorn==0.29.0` - ASGIサーバー

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

### 2025-12-20
- **新機能**: `/pinnedlist` スラッシュコマンドを追加
  - 自分または指定ユーザーのピン留めメッセージ一覧を表示
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

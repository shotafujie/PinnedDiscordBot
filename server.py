from threading import Thread
from fastapi import FastAPI
import uvicorn

# FastAPIアプリケーションのインスタンス作成
app = FastAPI(
    title="Discord Pin Bot Server",
    description="Koyeb用のDiscord Pin Botサーバー",
    version="1.0.0"
)

@app.get("/")
async def root():
    """
    ルートエンドポイント
    サーバーの動作確認用
    """
    return {
        "message": "Discord Pin Bot Server is Online.",
        "status": "running",
        "bot": "PinnedDiscordBot"
    }

@app.get("/health")
async def health_check():
    """
    ヘルスチェック用エンドポイント
    Koyebのヘルスチェック機能で使用
    """
    return {
        "status": "healthy",
        "service": "discord-pin-bot"
    }

@app.get("/status")
async def bot_status():
    """
    Bot状態確認用エンドポイント
    """
    return {
        "message": "Bot is running",
        "function": "Pin messages with pushpin reaction",
        "port": 8080
    }

def start_server():
    """
    uvicornサーバーを起動する関数
    Koyebの要求に従い0.0.0.0:8080でサーバーを起動
    """
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )

def server_thread():
    """
    サーバーを別スレッドで起動する関数
    メインのDiscord Botと並行してサーバーを動作させる
    """
    t = Thread(target=start_server, daemon=True)
    t.start()
    print("Koyeb用サーバーをポート8080で起動しました")

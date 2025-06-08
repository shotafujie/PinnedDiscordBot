import discord
from discord.ext import commands
import os
import asyncio
from aiohttp import web
import threading
import time

# Discord Bot設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has landed!')

@bot.event
async def on_raw_reaction_add(payload):
    # ピン留め絵文字（📌）をチェック
    if str(payload.emoji) == '📌':
        # チャンネルとメッセージを取得
        channel = bot.get_channel(payload.channel_id)
        if channel is None:
            return

        try:
            message = await channel.fetch_message(payload.message_id)

            # メッセージがすでにピン留めされているかチェック
            if not message.pinned:
                await message.pin()
                print(f"Message pinned in {channel.name}: {message.content[:50]}...")

        except discord.NotFound:
            print("Message not found")
        except discord.Forbidden:
            print("No permission to pin messages")
        except discord.HTTPException as e:
            print(f"Failed to pin message: {e}")

@bot.event
async def on_raw_reaction_remove(payload):
    # ピン留め絵文字が削除された場合
    if str(payload.emoji) == '📌':
        channel = bot.get_channel(payload.channel_id)
        if channel is None:
            return

        try:
            message = await channel.fetch_message(payload.message_id)

            # そのメッセージにピン留め絵文字がまだあるかチェック
            pin_reactions = [reaction for reaction in message.reactions if str(reaction.emoji) == '📌']

            # ピン留め絵文字がない場合、ピン留めを解除
            if not pin_reactions or pin_reactions[0].count == 0:
                if message.pinned:
                    await message.unpin()
                    print(f"Message unpinned in {channel.name}: {message.content[:50]}...")

        except discord.NotFound:
            print("Message not found")
        except discord.Forbidden:
            print("No permission to unpin messages")
        except discord.HTTPException as e:
            print(f"Failed to unpin message: {e}")

# Koyeb用のヘルスチェックサーバー（シンプル版）
def start_health_server():
    async def health_check(request):
        return web.Response(text="OK", status=200)

    async def init_app():
        app = web.Application()
        app.router.add_get('/', health_check)
        app.router.add_get('/health', health_check)

        port = int(os.environ.get('PORT', 8000))
        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"Health check server started on port {port}")

        # サーバーを永続的に動作させる
        while True:
            await asyncio.sleep(1)

    # 新しいイベントループで実行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_app())

def run_discord_bot():
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN environment variable not set")
        return

    try:
        bot.run(token)
    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    # ヘルスチェックサーバーを別スレッドで開始
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    # 少し待ってからDiscordBotを開始
    time.sleep(2)
    print("Starting Discord bot...")

    # メインスレッドでDiscordBotを実行
    run_discord_bot()

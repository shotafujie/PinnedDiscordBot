import discord
import os
import dotenv
from server import server_thread

# 環境変数の読み込み
dotenv.load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")

# Discordのインテントを設定
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # リアクションのイベントを受け取るために必要

client = discord.Client(intents=intents)

# ピン留め用の絵文字（pushpin）
PIN_EMOJI = "📌"

@client.event
async def on_ready():
    """
    Botが起動した時のイベント
    """
    print(f'{client.user} がログインしました!')
    print(f'Bot ID: {client.user.id}')
    print('📌 リアクションでメッセージをピン留めするBotが起動しました')

@client.event
async def on_reaction_add(reaction, user):
    """
    リアクションが追加された時のイベント
    📌(pushpin)リアクションが追加されたメッセージをピン留めする
    """
    # Botの反応は無視
    if user.bot:
        return

    # pushpin絵文字かどうかチェック
    if str(reaction.emoji) == PIN_EMOJI:
        message = reaction.message

        # 既にピン留めされているかチェック
        if message.pinned:
            print(f"メッセージ '{message.content[:50]}...' は既にピン留めされています")
            return

        try:
            # メッセージをピン留め
            await message.pin()

            # ログ出力
            print(f"メッセージをピン留めしました:")
            print(f"  チャンネル: {message.channel.name}")
            print(f"  作者: {message.author.name}")
            print(f"  内容: {message.content[:100]}...")
            print(f"  ピン留め実行者: {user.name}")

            # ピン留め実行を知らせる一時的なメッセージを送信
            pin_notification = await message.channel.send(
                f"📌 {user.mention} がメッセージをピン留めしました！"
            )

            # 5秒後に通知メッセージを削除
            import asyncio
            await asyncio.sleep(5)
            try:
                await pin_notification.delete()
            except discord.NotFound:
                pass  # 既に削除されている場合は無視

        except discord.Forbidden:
            # ピン留め権限がない場合
            await message.channel.send(
                f"❌ {user.mention} ピン留めする権限がありません。",
                delete_after=5
            )
        except discord.HTTPException as e:
            # その他のエラー（ピン留め数上限など）
            await message.channel.send(
                f"❌ {user.mention} ピン留めに失敗しました: {str(e)}",
                delete_after=5
            )

@client.event
async def on_reaction_remove(reaction, user):
    """
    リアクションが削除された時のイベント
    📌リアクションが削除されたらピン留めも解除する
    """
    # Botの反応は無視
    if user.bot:
        return

    # pushpin絵文字かどうかチェック
    if str(reaction.emoji) == PIN_EMOJI:
        message = reaction.message

        # ピン留めされていないなら何もしない
        if not message.pinned:
            return

        # 他にpushpinリアクションがあるかチェック
        pushpin_reactions = [r for r in message.reactions if str(r.emoji) == PIN_EMOJI]

        if not pushpin_reactions or pushpin_reactions[0].count <= 1:  # Bot分を除く
            try:
                # ピン留めを解除
                await message.unpin()

                print(f"ピン留めを解除しました:")
                print(f"  チャンネル: {message.channel.name}")
                print(f"  解除実行者: {user.name}")

                # ピン留め解除を知らせる一時的なメッセージを送信
                unpin_notification = await message.channel.send(
                    f"📌 {user.mention} がピン留めを解除しました。"
                )

                # 5秒後に通知メッセージを削除
                import asyncio
                await asyncio.sleep(5)
                try:
                    await unpin_notification.delete()
                except discord.NotFound:
                    pass

            except discord.Forbidden:
                await message.channel.send(
                    f"❌ {user.mention} ピン留めを解除する権限がありません。",
                    delete_after=5
                )
            except discord.HTTPException as e:
                await message.channel.send(
                    f"❌ {user.mention} ピン留め解除に失敗しました: {str(e)}",
                    delete_after=5
                )

@client.event
async def on_message(message):
    """
    メッセージが送信された時のイベント
    簡単なコマンドも用意
    """
    # Botの発言は無視
    if message.author.bot:
        return

    # ヘルプコマンド
    if message.content.lower() in ['!pin help', '!pinhelp']:
        help_message = """
📌 **Pin Bot の使い方**

このBotは 📌 (pushpin) リアクションでメッセージを簡単にピン留めできます！

**使い方:**
• ピン留めしたいメッセージに 📌 リアクションを付ける
• ピン留めを解除したい場合は 📌 リアクションを外す

**注意:**
• Botにピン留め権限が必要です
• 1チャンネルあたり最大50件までピン留めできます
        """
        await message.channel.send(help_message)

if __name__ == "__main__":
    # Koyeb用サーバーを起動
    server_thread()

    # Discord Botを起動
    if TOKEN:
        client.run(TOKEN)
    else:
        print("ERROR: TOKEN環境変数が設定されていません")

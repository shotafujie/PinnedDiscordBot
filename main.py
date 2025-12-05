import discord
import os
import dotenv
from server import server_thread
import asyncio

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
async def on_raw_reaction_add(payload):
    """
    リアクションが追加された時のイベント（キャッシュ不要版）
    📌(pushpin)リアクションが追加されたメッセージをピン留めする
    """
    # Botの反応は無視
    if payload.user_id == client.user.id:
        return

    # pushpin絵文字かどうかチェック
    if str(payload.emoji) == PIN_EMOJI:
        # チャンネルとメッセージを取得
        channel = client.get_channel(payload.channel_id)
        if channel is None:
            print(f"チャンネルが見つかりません (ID: {payload.channel_id})")
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            print(f"メッセージが見つかりません (ID: {payload.message_id})")
            return
        except discord.Forbidden:
            print(f"メッセージを取得する権限がありません")
            return

        # ユーザーを取得
        user = client.get_user(payload.user_id)
        if user is None:
            try:
                user = await client.fetch_user(payload.user_id)
            except:
                user = None

        # 既にピン留めされているかチェック
        if message.pinned:
            print(f"メッセージ '{message.content[:50]}...' は既にピン留めされています")
            return

        try:
            # メッセージをピン留め
            await message.pin()

            # ログ出力
            print(f"メッセージをピン留めしました:")
            print(f"  チャンネル: {channel.name}")
            print(f"  作者: {message.author.name}")
            print(f"  内容: {message.content[:100]}...")
            print(f"  ピン留め実行者: {user.name if user else payload.user_id}")
            print(f"  メッセージID: {message.id}")
            print(f"  メッセージ作成日時: {message.created_at}")

            # ピン留め実行を知らせる一時的なメッセージを送信
            user_mention = user.mention if user else f"<@{payload.user_id}>"
            pin_notification = await channel.send(
                f"📌 {user_mention} がメッセージをピン留めしました！"
            )

            # 5秒後に通知メッセージを削除
            await asyncio.sleep(5)
            try:
                await pin_notification.delete()
            except discord.NotFound:
                pass  # 既に削除されている場合は無視

        except discord.Forbidden:
            # ピン留め権限がない場合
            user_name = user.name if user else str(payload.user_id)
            user_mention = user.mention if user else f"<@{payload.user_id}>"
            print(f"権限エラー: ピン留め権限がありません (ユーザー: {user_name})")
            await channel.send(
                f"❌ {user_mention} ピン留めする権限がありません。",
                delete_after=5
            )
        except discord.HTTPException as e:
            # その他のエラー（ピン留め数上限など）
            user_mention = user.mention if user else f"<@{payload.user_id}>"
            print(f"HTTPエラー: {e}")
            await channel.send(
                f"❌ {user_mention} ピン留めに失敗しました: {str(e)}",
                delete_after=5
            )
        except Exception as e:
            # 予期しないエラー
            user_mention = user.mention if user else f"<@{payload.user_id}>"
            print(f"予期しないエラー: {e}")
            await channel.send(
                f"❌ {user_mention} 予期しないエラーが発生しました。",
                delete_after=5
            )

@client.event
async def on_raw_reaction_remove(payload):
    """
    リアクションが削除された時のイベント（キャッシュ不要版）
    📌リアクションが削除されたらピン留めも解除する
    """
    # Botの反応は無視
    if payload.user_id == client.user.id:
        return

    # pushpin絵文字かどうかチェック
    if str(payload.emoji) == PIN_EMOJI:
        # チャンネルとメッセージを取得
        channel = client.get_channel(payload.channel_id)
        if channel is None:
            print(f"チャンネルが見つかりません (ID: {payload.channel_id})")
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            print(f"メッセージが見つかりません (ID: {payload.message_id})")
            return
        except discord.Forbidden:
            print(f"メッセージを取得する権限がありません")
            return

        # ユーザーを取得
        user = client.get_user(payload.user_id)
        if user is None:
            try:
                user = await client.fetch_user(payload.user_id)
            except:
                user = None

        # ピン留めされていないなら何もしない
        if not message.pinned:
            print(f"メッセージは既にピン留めされていません (ID: {message.id})")
            return

        # 詳細なログ出力
        print(f"リアクション削除検知:")
        print(f"  チャンネル: {channel.name}")
        print(f"  メッセージID: {message.id}")
        print(f"  削除者: {user.name if user else payload.user_id}")

        # メッセージから最新のリアクション情報を取得
        # メッセージを再フェッチして最新の状態を確実に取得
        try:
            message = await channel.fetch_message(payload.message_id)
        except:
            pass

        should_unpin = False
        pushpin_reaction = None

        # 📌リアクションを探す
        for reaction in message.reactions:
            if str(reaction.emoji) == PIN_EMOJI:
                pushpin_reaction = reaction
                break

        if pushpin_reaction is None:
            # 📌リアクションが完全に削除された
            print("  📌リアクションが完全に削除されました")
            should_unpin = True
        else:
            # 実際のユーザー数をカウント（Bot以外）
            real_user_count = 0
            try:
                async for reaction_user in pushpin_reaction.users():
                    if not reaction_user.bot:
                        real_user_count += 1
                        print(f"    📌リアクションユーザー: {reaction_user.name}")

                print(f"  📌リアクション数: {pushpin_reaction.count} (Bot以外: {real_user_count})")

                if real_user_count == 0:
                    should_unpin = True
                    print("  Bot以外のリアクションがなくなりました")
            except Exception as e:
                print(f"  リアクションユーザー取得エラー: {e}")
                # エラーの場合は安全側に倒してカウントで判定
                if pushpin_reaction.count == 0:
                    should_unpin = True

        if should_unpin:
            try:
                # ピン留めを解除
                await message.unpin()

                user_name = user.name if user else str(payload.user_id)
                print(f"ピン留めを解除しました:")
                print(f"  チャンネル: {channel.name}")
                print(f"  解除実行者: {user_name}")
                print(f"  メッセージID: {message.id}")

                # ピン留め解除を知らせる一時的なメッセージを送信
                user_mention = user.mention if user else f"<@{payload.user_id}>"
                unpin_notification = await channel.send(
                    f"📌 {user_mention} がピン留めを解除しました。"
                )

                # 5秒後に通知メッセージを削除
                await asyncio.sleep(5)
                try:
                    await unpin_notification.delete()
                except discord.NotFound:
                    pass

            except discord.Forbidden:
                user_name = user.name if user else str(payload.user_id)
                user_mention = user.mention if user else f"<@{payload.user_id}>"
                print(f"権限エラー: ピン留め解除権限がありません (ユーザー: {user_name})")
                await channel.send(
                    f"❌ {user_mention} ピン留めを解除する権限がありません。",
                    delete_after=5
                )
            except discord.HTTPException as e:
                user_mention = user.mention if user else f"<@{payload.user_id}>"
                print(f"HTTPエラー: {e}")
                await channel.send(
                    f"❌ {user_mention} ピン留め解除に失敗しました: {str(e)}",
                    delete_after=5
                )
            except Exception as e:
                user_mention = user.mention if user else f"<@{payload.user_id}>"
                print(f"予期しないエラー: {e}")
                await channel.send(
                    f"❌ {user_mention} 予期しないエラーが発生しました。",
                    delete_after=5
                )
        else:
            print("  他のユーザーの📌リアクションが残っているため、ピン留めを維持します")

@client.event
async def on_error(event, *args, **kwargs):
    """
    エラーハンドリング
    """
    print(f"エラーが発生しました in {event}")
    import traceback
    traceback.print_exc()

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

**デバッグコマンド:**
• `!pin test` - 動作テスト
• `!pin status` - Bot状態確認
        """
        await message.channel.send(help_message)

    # テストコマンド
    elif message.content.lower() == '!pin test':
        test_msg = await message.channel.send("📌 このメッセージにリアクションしてテストしてください！")
        await test_msg.add_reaction(PIN_EMOJI)

    # ステータスコマンド
    elif message.content.lower() == '!pin status':
        try:
            pins = await message.channel.pins()
            await message.channel.send(
                f"**Bot状態:**\n"
                f"• Bot名: {client.user.name}\n"
                f"• 現在のピン留め数: {len(pins)}/50\n"
                f"• 権限: {'✅' if message.channel.permissions_for(message.guild.me).manage_messages else '❌'} メッセージ管理\n"
                f"• 稼働時間: {discord.utils.utcnow() - client.user.created_at}"
            )
        except Exception as e:
            await message.channel.send(f"ステータス取得エラー: {e}")

if __name__ == "__main__":
    # Koyeb用サーバーを起動
    server_thread()

    # Discord Botを起動
    if TOKEN:
        print("Discord Botを起動しています...")
        client.run(TOKEN)
    else:
        print("ERROR: DISCORD_TOKEN環境変数が設定されていません")

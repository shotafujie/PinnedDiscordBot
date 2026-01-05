import discord
from discord import app_commands
from discord.ext import commands
import os
import dotenv
from server import server_thread
import asyncio
from datetime import datetime, timedelta, timezone
from views.unpin_view import UnpinSelectView

# 環境変数の読み込み
dotenv.load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")

# Discordのインテントを設定
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # リアクションのイベントを受け取るために必要

# discord.ext.commands.Bot に移行（スラッシュコマンド対応）
bot = commands.Bot(command_prefix="!", intents=intents)

# ピン留め用の絵文字（pushpin）
PIN_EMOJI = "📌"


async def check_is_self_only_pin(pin, user_id):
    """ピン留めメッセージが自分だけのものかチェックする関数

    Args:
        pin: ピン留めメッセージオブジェクト
        user_id: チェックするユーザーのID

    Returns:
        bool: 自分だけがピン留めしている場合True
    """
    print(f"[DEBUG] check_is_self_only_pin: メッセージID={pin.id}, チェック対象ユーザーID={user_id}")
    print(f"[DEBUG] メッセージ内容: {pin.content[:30]}...")
    print(f"[DEBUG] リアクション数: {len(pin.reactions)}")

    pin_reaction = None
    for reaction in pin.reactions:
        print(f"[DEBUG] リアクション: {reaction.emoji} (count={reaction.count})")
        if str(reaction.emoji) == PIN_EMOJI:
            pin_reaction = reaction
            print(f"[DEBUG] 📌リアクションを発見！")
            break

    if pin_reaction is None:
        print(f"[DEBUG] 📌リアクションが見つかりませんでした")
        return False

    reaction_users = []
    async for user in pin_reaction.users():
        print(f"[DEBUG] リアクションユーザー: {user.name} (ID={user.id}, bot={user.bot})")
        if not user.bot:
            reaction_users.append(user)

    print(f"[DEBUG] Bot以外のリアクションユーザー数: {len(reaction_users)}")
    if len(reaction_users) > 0:
        print(f"[DEBUG] リアクションユーザーID: {[u.id for u in reaction_users]}")

    # 自分だけがリアクションしている場合のみTrue
    is_self_only = (
        len(reaction_users) == 1 and
        reaction_users[0].id == user_id
    )
    print(f"[DEBUG] 結果: is_self_only={is_self_only}")
    return is_self_only


@bot.event
async def on_ready():
    """
    Botが起動した時のイベント
    """
    print(f'{bot.user} がログインしました!')
    print(f'Bot ID: {bot.user.id}')
    print('📌 リアクションでメッセージをピン留めするBotが起動しました')

    # スラッシュコマンドを同期
    try:
        synced = await bot.tree.sync()
        print(f'スラッシュコマンドを {len(synced)} 個同期しました')
    except Exception as e:
        print(f'スラッシュコマンド同期エラー: {e}')


@bot.tree.command(name="pinnedlist", description="ピン留めメッセージの一覧を表示します")
@app_commands.describe(
    user="表示するユーザー（省略時は全員のメッセージ）",
    days="過去何日間のメッセージを表示するか（省略時は全期間）"
)
async def pinnedlist(
    interaction: discord.Interaction,
    user: discord.Member = None,
    days: int = None
):
    """
    ピン留めメッセージの一覧を表示し、自分だけがピン留めしているメッセージはまとめて解除できるスラッシュコマンド
    """
    await interaction.response.defer(ephemeral=True)

    try:
        # チャンネルのピン留めメッセージを取得
        pins = await interaction.channel.pins()

        # ユーザーでフィルタリング（指定がなければ全員）
        if user:
            filtered_pins = [p for p in pins if p.author.id == user.id]
            title_user = f"{user.display_name} さん"
        else:
            filtered_pins = pins
            title_user = "全員"

        # 日数でフィルタリング
        if days is not None and days > 0:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            filtered_pins = [p for p in filtered_pins if p.created_at >= cutoff_date]

        if not filtered_pins:
            period_text = f"過去{days}日間の" if days else ""
            target_text = f"{user.display_name} さんの" if user else ""
            await interaction.followup.send(
                f"📌 {target_text}{period_text}ピン留めメッセージはこのチャンネルにありません。",
                ephemeral=True
            )
            return

        # Embedを作成
        embed = discord.Embed(
            title=f"📌 {title_user}のピン留めメッセージ一覧",
            color=discord.Color.gold()
        )

        # メッセージリストを作成（リアクションベース判定）
        message_list = []
        my_pins = []  # 自分だけがピン留めしているメッセージ（解除用）
        my_id = interaction.user.id

        for pin in filtered_pins:
            # メッセージ冒頭の10文字を取得（改行を除去）
            content_preview = pin.content.replace('\n', ' ')[:10]
            if len(pin.content) > 10:
                content_preview += "..."

            # メッセージが空の場合（画像のみなど）
            if not content_preview.strip():
                content_preview = "[添付ファイル/埋め込み]"

            # メッセージリンクを作成
            message_link = f"https://discord.com/channels/{interaction.guild_id}/{pin.channel.id}/{pin.id}"

            # 自分だけがピン留めしているかチェック
            is_self_only = await check_is_self_only_pin(pin, my_id)

            if is_self_only:
                # 自分だけがピン留め: 解除可能
                message_list.append(f"📌 [{content_preview}]({message_link})")
                my_pins.append(pin)
            else:
                # 他人もピン留め or 自分はピン留めしていない: 解除不可
                message_list.append(f"🔒 [{content_preview}]({message_link}) *by {pin.author.display_name}*")

        # Embedの文字制限（4096文字）を考慮してリストを結合
        description = "\n".join(message_list)
        if len(description) > 4000:
            description = description[:4000] + "\n...（以降省略）"

        embed.description = description

        # フッターに件数を表示
        period_text = f"（過去{days}日間）" if days else ""
        total_count = len(filtered_pins)
        my_count = len(my_pins)

        footer_text = f"合計 {total_count} 件{period_text}"
        if my_count > 0:
            if my_count > 25:
                footer_text += f" | 📌 自分: {my_count}件（解除は先頭25件まで）"
            else:
                footer_text += f" | 📌 自分: {my_count}件（解除可能）"
        else:
            footer_text += " | 自分のピン留めはありません"

        embed.set_footer(text=footer_text)

        # 解除用のViewを作成（自分のメッセージのみ）
        if my_pins:
            view = UnpinSelectView(my_pins, user_id=my_id)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)

    except discord.Forbidden:
        await interaction.followup.send(
            "❌ ピン留めメッセージを取得する権限がありません。",
            ephemeral=True
        )
    except Exception as e:
        print(f"pinnedlistコマンドエラー: {e}")
        await interaction.followup.send(
            f"❌ エラーが発生しました: {str(e)}",
            ephemeral=True
        )


@bot.event
async def on_raw_reaction_add(payload):
    """
    リアクションが追加された時のイベント（キャッシュ不要版）
    📌(pushpin)リアクションが追加されたメッセージをピン留めする
    """
    # Botの反応は無視
    if payload.user_id == bot.user.id:
        return

    # pushpin絵文字かどうかチェック
    if str(payload.emoji) == PIN_EMOJI:
        # チャンネルとメッセージを取得
        channel = bot.get_channel(payload.channel_id)
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
        user = bot.get_user(payload.user_id)
        if user is None:
            try:
                user = await bot.fetch_user(payload.user_id)
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

@bot.event
async def on_raw_reaction_remove(payload):
    """
    リアクションが削除された時のイベント（キャッシュ不要版）
    📌リアクションが削除されたらピン留めも解除する
    """
    # Botの反応は無視
    if payload.user_id == bot.user.id:
        return

    # pushpin絵文字かどうかチェック
    if str(payload.emoji) == PIN_EMOJI:
        # チャンネルとメッセージを取得
        channel = bot.get_channel(payload.channel_id)
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
        user = bot.get_user(payload.user_id)
        if user is None:
            try:
                user = await bot.fetch_user(payload.user_id)
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

@bot.event
async def on_error(event, *args, **kwargs):
    """
    エラーハンドリング
    """
    print(f"エラーが発生しました in {event}")
    import traceback
    traceback.print_exc()

@bot.event
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

**スラッシュコマンド:**
• `/pinnedlist` - 全員のピン留めメッセージ一覧を表示
• `/pinnedlist user:@ユーザー` - 指定ユーザーのピン留めを表示
• `/pinnedlist days:7` - 過去7日間のピン留めメッセージを表示

**まとめて解除:**
自分だけがピン留めしているメッセージ（📌）は選択して一括解除できます。
他の人もピン留めしているメッセージ（🔒）は解除できません。

**注意:**
• Botにピン留め権限が必要です
• 1チャンネルあたり最大50件までピン留めできます
• まとめて解除は先頭25件まで選択可能です

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
                f"• Bot名: {bot.user.name}\n"
                f"• 現在のピン留め数: {len(pins)}/50\n"
                f"• 権限: {'✅' if message.channel.permissions_for(message.guild.me).manage_messages else '❌'} メッセージ管理\n"
                f"• 稼働時間: {discord.utils.utcnow() - bot.user.created_at}"
            )
        except Exception as e:
            await message.channel.send(f"ステータス取得エラー: {e}")

if __name__ == "__main__":
    # Koyeb用サーバーを起動
    server_thread()

    # Discord Botを起動
    if TOKEN:
        print("Discord Botを起動しています...")
        bot.run(TOKEN)
    else:
        print("ERROR: DISCORD_TOKEN環境変数が設定されていません")

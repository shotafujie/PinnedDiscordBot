import discord
from discord.ext import commands
import os
import asyncio

# Intentsの設定
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

# Botの初期化
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is ready and logged in as {bot.user}')

@bot.event
async def on_reaction_add(reaction, user):
    # Botのリアクションは無視
    if user.bot:
        return

    # 📌 (pushpin) エモジが追加された場合
    if str(reaction.emoji) == '📌':
        message = reaction.message

        # メッセージが既にピン留めされているかチェック
        if message.pinned:
            print(f"Message {message.id} is already pinned")
            return

        try:
            # メッセージをピン留め
            await message.pin()
            print(f"Pinned message {message.id} in channel {message.channel.name}")

            # ピン留め成功を通知（オプション）
            embed = discord.Embed(
                title="📌 メッセージをピン留めしました",
                description=f"[メッセージリンク]({message.jump_url})",
                color=0x00ff00
            )
            embed.set_footer(text=f"ピン留めしたユーザー: {user.display_name}")

            await message.channel.send(embed=embed, delete_after=10)

        except discord.Forbidden:
            # 権限がない場合
            await message.channel.send(
                f"{user.mention} ピン留めする権限がありません。",
                delete_after=5
            )
        except discord.HTTPException as e:
            # その他のエラー（ピン留め上限など）
            if e.code == 50019:  # Maximum number of pins reached
                await message.channel.send(
                    "このチャンネルはピン留めの上限に達しています。",
                    delete_after=5
                )
            else:
                await message.channel.send(
                    f"ピン留めに失敗しました: {str(e)}",
                    delete_after=5
                )

@bot.event
async def on_reaction_remove(reaction, user):
    # Botのリアクション削除は無視
    if user.bot:
        return

    # 📌 エモジが削除された場合
    if str(reaction.emoji) == '📌':
        message = reaction.message

        # メッセージがピン留めされていない場合は何もしない
        if not message.pinned:
            return

        # 他に📌リアクションがあるかチェック
        pin_reactions = [r for r in message.reactions if str(r.emoji) == '📌']

        if not pin_reactions or pin_reactions[0].count <= 1:  # Bot分を考慮
            try:
                # ピン留めを解除
                await message.unpin()
                print(f"Unpinned message {message.id} in channel {message.channel.name}")

                # ピン留め解除を通知（オプション）
                embed = discord.Embed(
                    title="📌 ピン留めを解除しました",
                    description=f"[メッセージリンク]({message.jump_url})",
                    color=0xff9900
                )
                embed.set_footer(text=f"解除したユーザー: {user.display_name}")

                await message.channel.send(embed=embed, delete_after=10)

            except discord.Forbidden:
                await message.channel.send(
                    f"{user.mention} ピン留めを解除する権限がありません。",
                    delete_after=5
                )
            except discord.HTTPException as e:
                await message.channel.send(
                    f"ピン留め解除に失敗しました: {str(e)}",
                    delete_after=5
                )

# ヘルプコマンド
@bot.command(name='pinhelp')
async def pin_help(ctx):
    embed = discord.Embed(
        title="📌 Pin Bot の使い方",
        description="メッセージに 📌 リアクションを付けるとピン留めされます。",
        color=0x0099ff
    )
    embed.add_field(
        name="使用方法",
        value="1. ピン留めしたいメッセージに 📌 をリアクション\n2. ピン留めを解除したい場合は 📌 リアクションを削除",
        inline=False
    )
    embed.add_field(
        name="注意事項",
        value="• Botに適切な権限が必要です\n• チャンネルごとにピン留めは50件まで\n• 通知メッセージは10秒後に自動削除されます",
        inline=False
    )

    await ctx.send(embed=embed)

# エラーハンドリング
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return  # コマンドが見つからない場合は無視

    print(f"Command error: {error}")

# Botの起動
if __name__ == "__main__":
    # 環境変数からトークンを取得
    token = os.getenv('DISCORD_TOKEN')

    if not token:
        print("Error: DISCORD_TOKEN environment variable not found!")
        print("Please set your Discord bot token as an environment variable.")
        exit(1)

    try:
        bot.run(token)
    except discord.LoginFailure:
        print("Error: Invalid Discord token!")
    except Exception as e:
        print(f"Error starting bot: {e}")

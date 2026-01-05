"""まとめてピン留め解除用のView/Select/Button"""
import discord
from discord import ui


class UnpinSelect(ui.Select):
    """ピン留め解除対象を選択するSelectMenu"""

    def __init__(self, pins: list):
        options = []
        for pin in pins[:25]:  # Discord制限: 最大25オプション
            content = pin.content.strip()
            if not content:
                label = "[添付ファイル]"
            elif len(content) > 100:
                label = content[:97] + "..."
            else:
                label = content

            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(pin.id),
                    description=f"投稿日: {pin.created_at.strftime('%Y-%m-%d %H:%M')}"
                )
            )

        super().__init__(
            placeholder="解除するメッセージを選択...",
            min_values=0,
            max_values=len(options),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_message_ids = [int(v) for v in self.values]
        await interaction.response.defer()


class ApplyButton(ui.Button):
    """適用ボタン"""

    def __init__(self):
        super().__init__(
            label="適用",
            style=discord.ButtonStyle.danger,
            custom_id="apply_unpin"
        )

    async def callback(self, interaction: discord.Interaction):
        view: UnpinSelectView = self.view
        selected_ids = view.selected_message_ids

        if not selected_ids:
            await interaction.response.edit_message(
                content="メッセージが選択されていません。",
                embed=None,
                view=None
            )
            return

        success_count = 0
        for msg_id in selected_ids:
            msg = view.pins_by_id.get(msg_id)
            if msg:
                try:
                    await msg.unpin()
                    success_count += 1
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass

        await interaction.response.edit_message(
            content=f"📌 {success_count}件のピン留めを解除しました。",
            embed=None,
            view=None
        )
        view.stop()


class CancelButton(ui.Button):
    """キャンセルボタン"""

    def __init__(self):
        super().__init__(
            label="キャンセル",
            style=discord.ButtonStyle.secondary,
            custom_id="cancel_unpin"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content="キャンセルしました。",
            embed=None,
            view=None
        )
        self.view.stop()


class UnpinSelectView(ui.View):
    """まとめてピン留め解除用のView"""

    def __init__(self, pins: list, user_id: int, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.pins = pins
        self.user_id = user_id
        self.selected_message_ids: list[int] = []
        self.pins_by_id = {pin.id: pin for pin in pins}

        self.add_item(UnpinSelect(pins))
        self.add_item(ApplyButton())
        self.add_item(CancelButton())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """コマンド実行者のみ操作可能"""
        return interaction.user.id == self.user_id

    async def on_timeout(self):
        """タイムアウト時の処理"""
        pass

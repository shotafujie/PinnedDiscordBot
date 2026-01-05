"""pinnedlistコマンドのユニットテスト"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import sys

sys.path.insert(0, '/Users/fujiemon/dev/PinnedDiscordBot')


@pytest.fixture
def mock_bot():
    """モックBotオブジェクト"""
    bot = MagicMock()
    bot.user = MagicMock()
    bot.user.id = 999999999
    return bot


@pytest.fixture
def mock_interaction():
    """モックInteractionオブジェクト"""
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 111111111  # コマンド実行者のID
    interaction.user.display_name = "CommandUser"
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    interaction.channel = MagicMock()
    interaction.channel.pins = AsyncMock()
    interaction.guild_id = 123456
    return interaction


def create_mock_reaction(emoji, users):
    """モックReactionオブジェクトを作成

    Args:
        emoji: リアクション絵文字
        users: リアクションしたユーザーのリスト
    """
    reaction = MagicMock()
    reaction.emoji = emoji
    reaction.count = len(users)

    async def users_generator():
        for user in users:
            yield user

    reaction.users = lambda: users_generator()
    return reaction


def create_mock_pin(pin_id, content, author_id, author_name, reactions):
    """モックピン留めメッセージを作成

    Args:
        pin_id: メッセージID
        content: メッセージ内容
        author_id: 作成者のID
        author_name: 作成者の名前
        reactions: リアクションのリスト
    """
    pin = MagicMock()
    pin.id = pin_id
    pin.content = content
    pin.author = MagicMock()
    pin.author.id = author_id
    pin.author.display_name = author_name
    pin.created_at = datetime.now(timezone.utc)
    pin.channel = MagicMock()
    pin.channel.id = 222222
    pin.reactions = reactions
    pin.unpin = AsyncMock()
    return pin


def create_mock_user(user_id, user_name, is_bot=False):
    """モックUserオブジェクトを作成"""
    user = MagicMock()
    user.id = user_id
    user.name = user_name
    user.display_name = user_name
    user.bot = is_bot
    return user


async def check_is_self_only_pin(pin, user_id):
    """ピン留めメッセージが自分だけのものかチェックする関数

    Args:
        pin: ピン留めメッセージオブジェクト
        user_id: チェックするユーザーのID

    Returns:
        bool: 自分だけがピン留めしている場合True
    """
    pin_reaction = None
    for reaction in pin.reactions:
        if str(reaction.emoji) == "📌":
            pin_reaction = reaction
            break

    if pin_reaction is None:
        return False

    reaction_users = []
    async for user in pin_reaction.users():
        if not user.bot:
            reaction_users.append(user)

    # 自分だけがリアクションしている場合のみTrue
    return (
        len(reaction_users) == 1 and
        reaction_users[0].id == user_id
    )


class TestPinnedListReactionBasedLogic:
    """pinnedlistコマンドのリアクションベース判定ロジックのテスト"""

    @pytest.mark.asyncio
    async def test_self_only_reaction_shows_pin_emoji(self, mock_interaction):
        """自分だけが📌リアクションしているメッセージは📌で表示"""
        # 準備: 自分だけがリアクションしているメッセージ
        command_user = create_mock_user(111111111, "CommandUser")
        reactions = [create_mock_reaction("📌", [command_user])]
        pin = create_mock_pin(
            pin_id=123,
            content="自分だけがピン留め",
            author_id=999999999,  # 他人が投稿
            author_name="OtherUser",
            reactions=reactions
        )

        # 実行
        is_self_only = await check_is_self_only_pin(pin, mock_interaction.user.id)

        # 期待: 自分だけがリアクションしているのでTrue
        assert is_self_only is True

    @pytest.mark.asyncio
    async def test_self_and_others_reaction_shows_lock_emoji(self, mock_interaction):
        """自分+他人が📌リアクションしているメッセージは🔒で表示"""
        # 準備: 自分と他人がリアクションしているメッセージ
        command_user = create_mock_user(111111111, "CommandUser")
        other_user = create_mock_user(222222222, "OtherUser")
        reactions = [create_mock_reaction("📌", [command_user, other_user])]
        pin = create_mock_pin(
            pin_id=124,
            content="複数人がピン留め",
            author_id=111111111,  # 自分が投稿
            author_name="CommandUser",
            reactions=reactions
        )

        # 実行
        is_self_only = await check_is_self_only_pin(pin, mock_interaction.user.id)

        # 期待: 他人もリアクションしているのでFalse
        assert is_self_only is False

    @pytest.mark.asyncio
    async def test_others_only_reaction_shows_lock_emoji(self, mock_interaction):
        """他人だけが📌リアクションしているメッセージは🔒で表示"""
        # 準備: 他人だけがリアクションしているメッセージ
        other_user = create_mock_user(222222222, "OtherUser")
        reactions = [create_mock_reaction("📌", [other_user])]
        pin = create_mock_pin(
            pin_id=125,
            content="他人だけがピン留め",
            author_id=111111111,  # 自分が投稿
            author_name="CommandUser",
            reactions=reactions
        )

        # 実行
        is_self_only = await check_is_self_only_pin(pin, mock_interaction.user.id)

        # 期待: 自分はリアクションしていないのでFalse
        assert is_self_only is False

    @pytest.mark.asyncio
    async def test_no_pushpin_reaction_shows_lock_emoji(self, mock_interaction):
        """📌リアクションがないメッセージは🔒で表示"""
        # 準備: 📌リアクションがないメッセージ（他の絵文字のみ）
        command_user = create_mock_user(111111111, "CommandUser")
        reactions = [create_mock_reaction("👍", [command_user])]
        pin = create_mock_pin(
            pin_id=126,
            content="📌リアクションなし",
            author_id=111111111,  # 自分が投稿
            author_name="CommandUser",
            reactions=reactions
        )

        # 実行
        is_self_only = await check_is_self_only_pin(pin, mock_interaction.user.id)

        # 期待: 📌リアクションがないのでFalse
        assert is_self_only is False

    @pytest.mark.asyncio
    async def test_bot_reactions_are_ignored(self, mock_interaction):
        """Botのリアクションは無視される"""
        # 準備: 自分とBotがリアクションしているメッセージ
        command_user = create_mock_user(111111111, "CommandUser")
        bot_user = create_mock_user(999999999, "BotUser", is_bot=True)
        reactions = [create_mock_reaction("📌", [command_user, bot_user])]
        pin = create_mock_pin(
            pin_id=127,
            content="自分とBotがピン留め",
            author_id=222222222,  # 他人が投稿
            author_name="OtherUser",
            reactions=reactions
        )

        # 実行
        is_self_only = await check_is_self_only_pin(pin, mock_interaction.user.id)

        # 期待: Botを除外すると自分だけなのでTrue
        assert is_self_only is True

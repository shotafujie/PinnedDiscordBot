import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone


@pytest.fixture
def mock_message():
    """モック Message オブジェクト"""
    message = MagicMock()
    message.id = 123456789
    message.content = "テストメッセージの内容です"
    message.author = MagicMock()
    message.author.id = 111111111
    message.author.name = "TestUser"
    message.pinned = True
    message.unpin = AsyncMock()
    message.created_at = datetime.now(timezone.utc)
    message.jump_url = "https://discord.com/channels/1/2/123456789"
    return message


@pytest.fixture
def mock_interaction():
    """モック Interaction オブジェクト"""
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 111111111
    interaction.user.name = "TestUser"
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    interaction.edit_original_response = AsyncMock()
    interaction.channel = MagicMock()
    interaction.channel.fetch_message = AsyncMock()
    return interaction


@pytest.fixture
def mock_pins(mock_message):
    """複数のモックピン留めメッセージ"""
    pins = []
    for i in range(5):
        pin = MagicMock()
        pin.id = 123456789 + i
        pin.content = f"ピン留めメッセージ {i + 1}"
        pin.author = MagicMock()
        pin.author.id = 111111111
        pin.author.name = "TestUser"
        pin.pinned = True
        pin.unpin = AsyncMock()
        pin.created_at = datetime.now(timezone.utc)
        pin.jump_url = f"https://discord.com/channels/1/2/{pin.id}"
        pins.append(pin)
    return pins

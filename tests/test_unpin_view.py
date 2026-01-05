"""UnpinSelectView のユニットテスト"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone

import sys
sys.path.insert(0, '/Users/fujiemon/dev/PinnedDiscordBot')

from views.unpin_view import UnpinSelect, UnpinSelectView


class TestUnpinSelect:
    """UnpinSelect のテスト"""

    def test_options_created_from_pins(self, mock_pins):
        """ピン留めメッセージからSelectOptionが正しく生成される"""
        select = UnpinSelect(mock_pins)

        assert len(select.options) == 5
        assert select.options[0].value == str(mock_pins[0].id)
        assert "ピン留めメッセージ 1" in select.options[0].label

    def test_max_25_options(self):
        """26件以上でも最大25件に制限される"""
        pins = []
        for i in range(30):
            pin = MagicMock()
            pin.id = 100 + i
            pin.content = f"メッセージ {i}"
            pin.created_at = datetime.now(timezone.utc)
            pins.append(pin)

        select = UnpinSelect(pins)

        assert len(select.options) == 25

    def test_empty_content_shows_attachment_label(self):
        """空コンテンツ（画像のみ）の場合は[添付ファイル]と表示"""
        pin = MagicMock()
        pin.id = 999
        pin.content = ""
        pin.created_at = datetime.now(timezone.utc)

        select = UnpinSelect([pin])

        assert "[添付ファイル]" in select.options[0].label

    def test_long_content_truncated(self):
        """長いコンテンツは切り詰められる"""
        pin = MagicMock()
        pin.id = 999
        pin.content = "a" * 200
        pin.created_at = datetime.now(timezone.utc)

        select = UnpinSelect([pin])

        assert len(select.options[0].label) <= 100

    def test_multiple_selection_enabled(self, mock_pins):
        """複数選択が有効になっている"""
        select = UnpinSelect(mock_pins)

        assert select.max_values == len(mock_pins)
        assert select.min_values == 0


class TestUnpinSelectView:
    """UnpinSelectView のテスト"""

    async def test_view_has_select_and_buttons(self, mock_pins):
        """ViewにSelect、適用ボタン、キャンセルボタンが含まれる"""
        view = UnpinSelectView(mock_pins, user_id=111111111)

        # コンポーネント数をチェック（Select + Button x 2）
        assert len(view.children) == 3

    async def test_interaction_check_allows_owner(self, mock_pins, mock_interaction):
        """コマンド実行者は操作可能"""
        view = UnpinSelectView(mock_pins, user_id=111111111)
        mock_interaction.user.id = 111111111

        result = await view.interaction_check(mock_interaction)

        assert result is True

    async def test_interaction_check_denies_others(self, mock_pins, mock_interaction):
        """コマンド実行者以外は操作不可"""
        view = UnpinSelectView(mock_pins, user_id=111111111)
        mock_interaction.user.id = 999999999  # 別のユーザー

        result = await view.interaction_check(mock_interaction)

        assert result is False


class TestCancelButton:
    """CancelButton のテスト"""

    async def test_cancel_button_clears_view(self, mock_pins, mock_interaction):
        """キャンセルボタンでViewがクリアされる"""
        from views.unpin_view import CancelButton

        view = UnpinSelectView(mock_pins, user_id=111111111)
        cancel_button = None
        for child in view.children:
            if isinstance(child, CancelButton):
                cancel_button = child
                break

        assert cancel_button is not None

        await cancel_button.callback(mock_interaction)

        mock_interaction.response.edit_message.assert_called_once()
        call_kwargs = mock_interaction.response.edit_message.call_args.kwargs
        assert "キャンセル" in call_kwargs["content"]
        assert call_kwargs["view"] is None


class TestApplyButton:
    """ApplyButton のテスト"""

    async def test_apply_button_unpins_selected(self, mock_pins, mock_interaction):
        """適用ボタンで選択メッセージがunpinされる"""
        from views.unpin_view import ApplyButton

        view = UnpinSelectView(mock_pins, user_id=111111111)
        view.selected_message_ids = [mock_pins[0].id, mock_pins[1].id]

        apply_button = None
        for child in view.children:
            if isinstance(child, ApplyButton):
                apply_button = child
                break

        assert apply_button is not None

        await apply_button.callback(mock_interaction)

        # unpin が呼ばれたことを確認
        mock_pins[0].unpin.assert_called_once()
        mock_pins[1].unpin.assert_called_once()
        # 他のピンは呼ばれていない
        mock_pins[2].unpin.assert_not_called()

        # 結果メッセージを確認
        call_kwargs = mock_interaction.response.edit_message.call_args.kwargs
        assert "2件" in call_kwargs["content"]

    async def test_apply_button_no_selection(self, mock_pins, mock_interaction):
        """未選択時はエラーメッセージ"""
        from views.unpin_view import ApplyButton

        view = UnpinSelectView(mock_pins, user_id=111111111)
        view.selected_message_ids = []

        apply_button = None
        for child in view.children:
            if isinstance(child, ApplyButton):
                apply_button = child
                break

        await apply_button.callback(mock_interaction)

        call_kwargs = mock_interaction.response.edit_message.call_args.kwargs
        assert "選択されていません" in call_kwargs["content"]

    async def test_apply_button_handles_forbidden_error(self, mock_pins, mock_interaction):
        """unpin権限エラー時も他のメッセージは処理される"""
        import discord
        from views.unpin_view import ApplyButton

        # 1つ目のピンはForbiddenエラー
        mock_pins[0].unpin = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "No permission"))
        # 2つ目は成功
        mock_pins[1].unpin = AsyncMock()

        view = UnpinSelectView(mock_pins, user_id=111111111)
        view.selected_message_ids = [mock_pins[0].id, mock_pins[1].id]

        apply_button = None
        for child in view.children:
            if isinstance(child, ApplyButton):
                apply_button = child
                break

        await apply_button.callback(mock_interaction)

        # 両方呼ばれたが、成功は1件のみ
        mock_pins[0].unpin.assert_called_once()
        mock_pins[1].unpin.assert_called_once()
        call_kwargs = mock_interaction.response.edit_message.call_args.kwargs
        assert "1件" in call_kwargs["content"]


class TestViewTimeout:
    """View タイムアウトのテスト"""

    async def test_view_has_timeout(self, mock_pins):
        """Viewにタイムアウトが設定されている"""
        view = UnpinSelectView(mock_pins, user_id=111111111)
        assert view.timeout == 180.0

    async def test_view_custom_timeout(self, mock_pins):
        """カスタムタイムアウトを設定できる"""
        view = UnpinSelectView(mock_pins, user_id=111111111, timeout=60.0)
        assert view.timeout == 60.0

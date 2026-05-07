"""Tests for the Sticker Chart store."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.sticker_chart.store import StickerChartStore


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    return hass


@pytest.fixture
def store(mock_hass):
    """Create a store with mocked storage."""
    with patch(
        "custom_components.sticker_chart.store.Store"
    ) as mock_store_cls:
        mock_store_instance = MagicMock()
        mock_store_instance.async_load = AsyncMock(return_value=None)
        mock_store_instance.async_save = AsyncMock()
        mock_store_cls.return_value = mock_store_instance

        s = StickerChartStore(mock_hass)
        return s


@pytest.fixture
async def loaded_store(store):
    """Create a store that's been loaded."""
    await store.async_load()
    return store


# --- Children ---


@pytest.mark.asyncio
async def test_add_child(loaded_store):
    """Test adding a child."""
    child_id = await loaded_store.async_add_child("Alice")
    assert child_id is not None
    assert len(child_id) == 8
    assert loaded_store.children[child_id]["name"] == "Alice"
    assert loaded_store.children[child_id]["stickers"] == 0


@pytest.mark.asyncio
async def test_remove_child(loaded_store):
    """Test removing a child."""
    child_id = await loaded_store.async_add_child("Bob")
    await loaded_store.async_remove_child(child_id)
    assert child_id not in loaded_store.children


@pytest.mark.asyncio
async def test_remove_nonexistent_child(loaded_store):
    """Test removing a child that doesn't exist."""
    with pytest.raises(ValueError, match="not found"):
        await loaded_store.async_remove_child("nonexistent")


@pytest.mark.asyncio
async def test_remove_child_cleans_pending_requests(loaded_store):
    """Test that removing a child removes their pending requests."""
    child_id = await loaded_store.async_add_child("Charlie")
    reward_id = await loaded_store.async_add_reward("Treat", 1)
    await loaded_store.async_grant_stickers(child_id, 10)
    request_id = await loaded_store.async_request_redemption(child_id, reward_id)
    assert request_id in loaded_store.pending_requests

    await loaded_store.async_remove_child(child_id)
    assert request_id not in loaded_store.pending_requests


# --- Stickers ---


@pytest.mark.asyncio
async def test_grant_stickers(loaded_store):
    """Test granting stickers."""
    child_id = await loaded_store.async_add_child("Alice")
    balance = await loaded_store.async_grant_stickers(child_id, 5, "Good job")
    assert balance == 5
    assert loaded_store.get_child_balance(child_id) == 5


@pytest.mark.asyncio
async def test_grant_stickers_accumulate(loaded_store):
    """Test that stickers accumulate."""
    child_id = await loaded_store.async_add_child("Alice")
    await loaded_store.async_grant_stickers(child_id, 5)
    balance = await loaded_store.async_grant_stickers(child_id, 3)
    assert balance == 8


@pytest.mark.asyncio
async def test_grant_stickers_invalid_amount(loaded_store):
    """Test granting zero or negative stickers fails."""
    child_id = await loaded_store.async_add_child("Alice")
    with pytest.raises(ValueError, match="positive"):
        await loaded_store.async_grant_stickers(child_id, 0)
    with pytest.raises(ValueError, match="positive"):
        await loaded_store.async_grant_stickers(child_id, -1)


@pytest.mark.asyncio
async def test_revoke_stickers(loaded_store):
    """Test revoking stickers."""
    child_id = await loaded_store.async_add_child("Alice")
    await loaded_store.async_grant_stickers(child_id, 10)
    balance = await loaded_store.async_revoke_stickers(child_id, 3, "Misbehaved")
    assert balance == 7


@pytest.mark.asyncio
async def test_revoke_stickers_floors_at_zero(loaded_store):
    """Test that revoking more stickers than available floors at 0."""
    child_id = await loaded_store.async_add_child("Alice")
    await loaded_store.async_grant_stickers(child_id, 5)
    balance = await loaded_store.async_revoke_stickers(child_id, 100)
    assert balance == 0


@pytest.mark.asyncio
async def test_revoke_stickers_invalid_amount(loaded_store):
    """Test revoking zero or negative stickers fails."""
    child_id = await loaded_store.async_add_child("Alice")
    with pytest.raises(ValueError, match="positive"):
        await loaded_store.async_revoke_stickers(child_id, 0)


# --- Rewards ---


@pytest.mark.asyncio
async def test_add_reward(loaded_store):
    """Test adding a reward."""
    reward_id = await loaded_store.async_add_reward("Ice Cream", 10, "mdi:ice-cream")
    assert reward_id is not None
    assert loaded_store.rewards[reward_id]["name"] == "Ice Cream"
    assert loaded_store.rewards[reward_id]["cost"] == 10
    assert loaded_store.rewards[reward_id]["icon"] == "mdi:ice-cream"
    assert loaded_store.rewards[reward_id]["automation_id"] is None


@pytest.mark.asyncio
async def test_add_reward_with_automation(loaded_store):
    """Test adding a reward with an automation ID."""
    reward_id = await loaded_store.async_add_reward(
        "Screen Time", 20, "mdi:television", "automation.grant_screen_time"
    )
    assert loaded_store.rewards[reward_id]["automation_id"] == "automation.grant_screen_time"


@pytest.mark.asyncio
async def test_add_reward_invalid_cost(loaded_store):
    """Test adding a reward with invalid cost."""
    with pytest.raises(ValueError, match="positive"):
        await loaded_store.async_add_reward("Bad Reward", 0)
    with pytest.raises(ValueError, match="positive"):
        await loaded_store.async_add_reward("Bad Reward", -5)


@pytest.mark.asyncio
async def test_remove_reward(loaded_store):
    """Test removing a reward."""
    reward_id = await loaded_store.async_add_reward("Treat", 5)
    await loaded_store.async_remove_reward(reward_id)
    assert reward_id not in loaded_store.rewards


@pytest.mark.asyncio
async def test_update_reward(loaded_store):
    """Test updating a reward."""
    reward_id = await loaded_store.async_add_reward("Treat", 5)
    await loaded_store.async_update_reward(reward_id, name="Big Treat", cost=15)
    assert loaded_store.rewards[reward_id]["name"] == "Big Treat"
    assert loaded_store.rewards[reward_id]["cost"] == 15


@pytest.mark.asyncio
async def test_update_reward_invalid_field(loaded_store):
    """Test updating a reward with invalid field."""
    reward_id = await loaded_store.async_add_reward("Treat", 5)
    with pytest.raises(ValueError, match="Invalid"):
        await loaded_store.async_update_reward(reward_id, bogus="value")


# --- Redemption ---


@pytest.mark.asyncio
async def test_request_redemption(loaded_store):
    """Test requesting a reward redemption."""
    child_id = await loaded_store.async_add_child("Alice")
    reward_id = await loaded_store.async_add_reward("Treat", 5)
    await loaded_store.async_grant_stickers(child_id, 10)

    request_id = await loaded_store.async_request_redemption(child_id, reward_id)
    assert request_id in loaded_store.pending_requests
    assert loaded_store.pending_requests[request_id]["child_id"] == child_id
    assert loaded_store.pending_requests[request_id]["reward_id"] == reward_id


@pytest.mark.asyncio
async def test_request_redemption_insufficient_funds(loaded_store):
    """Test requesting a reward without enough stickers."""
    child_id = await loaded_store.async_add_child("Alice")
    reward_id = await loaded_store.async_add_reward("Expensive", 100)
    await loaded_store.async_grant_stickers(child_id, 5)

    with pytest.raises(ValueError, match="Not enough stickers"):
        await loaded_store.async_request_redemption(child_id, reward_id)


@pytest.mark.asyncio
async def test_request_redemption_duplicate_blocked(loaded_store):
    """Test that duplicate pending requests are blocked."""
    child_id = await loaded_store.async_add_child("Alice")
    reward_id = await loaded_store.async_add_reward("Treat", 5)
    await loaded_store.async_grant_stickers(child_id, 20)

    await loaded_store.async_request_redemption(child_id, reward_id)
    with pytest.raises(ValueError, match="pending request"):
        await loaded_store.async_request_redemption(child_id, reward_id)


@pytest.mark.asyncio
async def test_approve_redemption(loaded_store):
    """Test approving a redemption."""
    child_id = await loaded_store.async_add_child("Alice")
    reward_id = await loaded_store.async_add_reward("Treat", 5, automation_id="automation.test")
    await loaded_store.async_grant_stickers(child_id, 10)

    request_id = await loaded_store.async_request_redemption(child_id, reward_id)
    result = await loaded_store.async_approve_redemption(request_id)

    assert result["child_name"] == "Alice"
    assert result["reward_name"] == "Treat"
    assert result["reward_cost"] == 5
    assert result["automation_id"] == "automation.test"
    assert result["new_balance"] == 5
    assert loaded_store.get_child_balance(child_id) == 5
    assert request_id not in loaded_store.pending_requests


@pytest.mark.asyncio
async def test_approve_redemption_insufficient_funds_after_request(loaded_store):
    """Test that approval fails if stickers were spent after requesting."""
    child_id = await loaded_store.async_add_child("Alice")
    reward_id = await loaded_store.async_add_reward("Treat", 5)
    await loaded_store.async_grant_stickers(child_id, 6)

    request_id = await loaded_store.async_request_redemption(child_id, reward_id)
    # Revoke stickers after the request
    await loaded_store.async_revoke_stickers(child_id, 5)

    with pytest.raises(ValueError, match="Not enough stickers"):
        await loaded_store.async_approve_redemption(request_id)


@pytest.mark.asyncio
async def test_deny_redemption(loaded_store):
    """Test denying a redemption."""
    child_id = await loaded_store.async_add_child("Alice")
    reward_id = await loaded_store.async_add_reward("Treat", 5)
    await loaded_store.async_grant_stickers(child_id, 10)

    request_id = await loaded_store.async_request_redemption(child_id, reward_id)
    result = await loaded_store.async_deny_redemption(request_id)

    assert result["child_name"] == "Alice"
    assert result["reward_name"] == "Treat"
    assert loaded_store.get_child_balance(child_id) == 10  # Untouched
    assert request_id not in loaded_store.pending_requests


# --- History ---


@pytest.mark.asyncio
async def test_history_recorded(loaded_store):
    """Test that grant/revoke/redeem are recorded in history."""
    child_id = await loaded_store.async_add_child("Alice")
    reward_id = await loaded_store.async_add_reward("Treat", 5)

    await loaded_store.async_grant_stickers(child_id, 10, "Good job")
    await loaded_store.async_revoke_stickers(child_id, 2, "Oops")

    request_id = await loaded_store.async_request_redemption(child_id, reward_id)
    await loaded_store.async_approve_redemption(request_id)

    history = loaded_store.get_child_history(child_id)
    assert len(history) == 3
    assert history[0]["type"] == "grant"
    assert history[0]["amount"] == 10
    assert history[0]["reason"] == "Good job"
    assert history[1]["type"] == "revoke"
    assert history[1]["amount"] == 2
    assert history[2]["type"] == "redeem"
    assert history[2]["amount"] == 5


@pytest.mark.asyncio
async def test_pending_requests_for_child(loaded_store):
    """Test getting pending requests for a specific child."""
    child_id = await loaded_store.async_add_child("Alice")
    reward_id = await loaded_store.async_add_reward("Treat", 5)
    await loaded_store.async_grant_stickers(child_id, 20)

    await loaded_store.async_request_redemption(child_id, reward_id)
    pending = loaded_store.get_pending_requests_for_child(child_id)
    assert len(pending) == 1
    assert pending[0]["reward_name"] == "Treat"


# --- Storage Load ---


@pytest.mark.asyncio
async def test_load_existing_data(mock_hass):
    """Test loading existing stored data."""
    existing_data = {
        "children": {"abc": {"name": "Alice", "stickers": 42}},
        "rewards": {"xyz": {"name": "Treat", "cost": 5, "icon": "mdi:star", "automation_id": None}},
        "pending_requests": {},
        "history": [],
    }
    with patch(
        "custom_components.sticker_chart.store.Store"
    ) as mock_store_cls:
        mock_store_instance = MagicMock()
        mock_store_instance.async_load = AsyncMock(return_value=existing_data)
        mock_store_instance.async_save = AsyncMock()
        mock_store_cls.return_value = mock_store_instance

        store = StickerChartStore(mock_hass)
        await store.async_load()

        assert store.get_child_balance("abc") == 42
        assert store.rewards["xyz"]["name"] == "Treat"

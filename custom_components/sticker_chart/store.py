"""Persistent storage for the Sticker Chart integration."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)


def _new_id() -> str:
    """Generate a short unique ID."""
    return uuid.uuid4().hex[:8]


def _now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


class StickerChartStore:
    """Manage persistent storage for sticker chart data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the store."""
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, Any] = {}

    async def async_load(self) -> None:
        """Load data from disk."""
        stored = await self._store.async_load()
        if stored is None:
            self._data = {
                "children": {},
                "rewards": {},
                "pending_requests": {},
                "history": [],
            }
        else:
            self._data = stored
            # Ensure all keys exist for upgrades
            self._data.setdefault("children", {})
            self._data.setdefault("rewards", {})
            self._data.setdefault("pending_requests", {})
            self._data.setdefault("history", [])

    async def _async_save(self) -> None:
        """Persist data to disk."""
        await self._store.async_save(self._data)

    # --- Children ---

    @property
    def children(self) -> dict[str, dict[str, Any]]:
        """Return all children."""
        return self._data["children"]

    async def async_add_child(self, name: str) -> str:
        """Add a child and return their ID."""
        child_id = _new_id()
        self._data["children"][child_id] = {
            "name": name,
            "stickers": 0,
        }
        await self._async_save()
        _LOGGER.info("Added child %s (%s)", name, child_id)
        return child_id

    async def async_remove_child(self, child_id: str) -> None:
        """Remove a child and their pending requests."""
        if child_id not in self._data["children"]:
            raise ValueError(f"Child {child_id} not found")
        name = self._data["children"][child_id]["name"]
        del self._data["children"][child_id]
        # Clean up pending requests for this child
        to_remove = [
            rid
            for rid, req in self._data["pending_requests"].items()
            if req["child_id"] == child_id
        ]
        for rid in to_remove:
            del self._data["pending_requests"][rid]
        await self._async_save()
        _LOGGER.info("Removed child %s (%s)", name, child_id)

    async def async_grant_stickers(
        self, child_id: str, amount: int, reason: str = ""
    ) -> int:
        """Grant stickers to a child. Returns new balance."""
        if child_id not in self._data["children"]:
            raise ValueError(f"Child {child_id} not found")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self._data["children"][child_id]["stickers"] += amount
        self._data["history"].append(
            {
                "type": "grant",
                "child_id": child_id,
                "amount": amount,
                "reason": reason,
                "timestamp": _now_iso(),
            }
        )
        await self._async_save()
        return self._data["children"][child_id]["stickers"]

    async def async_revoke_stickers(
        self, child_id: str, amount: int, reason: str = ""
    ) -> int:
        """Revoke stickers from a child. Balance floors at 0. Returns new balance."""
        if child_id not in self._data["children"]:
            raise ValueError(f"Child {child_id} not found")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        current = self._data["children"][child_id]["stickers"]
        self._data["children"][child_id]["stickers"] = max(0, current - amount)
        self._data["history"].append(
            {
                "type": "revoke",
                "child_id": child_id,
                "amount": amount,
                "reason": reason,
                "timestamp": _now_iso(),
            }
        )
        await self._async_save()
        return self._data["children"][child_id]["stickers"]

    def get_child_balance(self, child_id: str) -> int:
        """Get a child's sticker balance."""
        if child_id not in self._data["children"]:
            raise ValueError(f"Child {child_id} not found")
        return self._data["children"][child_id]["stickers"]

    def get_child_name(self, child_id: str) -> str:
        """Get a child's name."""
        if child_id not in self._data["children"]:
            raise ValueError(f"Child {child_id} not found")
        return self._data["children"][child_id]["name"]

    # --- Rewards ---

    @property
    def rewards(self) -> dict[str, dict[str, Any]]:
        """Return all rewards."""
        return self._data["rewards"]

    async def async_add_reward(
        self,
        name: str,
        cost: int,
        icon: str = "mdi:star",
        automation_id: str | None = None,
    ) -> str:
        """Add a reward and return its ID."""
        if cost <= 0:
            raise ValueError("Cost must be positive")
        reward_id = _new_id()
        self._data["rewards"][reward_id] = {
            "name": name,
            "cost": cost,
            "icon": icon,
            "automation_id": automation_id,
        }
        await self._async_save()
        _LOGGER.info("Added reward %s (%s) costing %d stickers", name, reward_id, cost)
        return reward_id

    async def async_remove_reward(self, reward_id: str) -> None:
        """Remove a reward and any pending requests for it."""
        if reward_id not in self._data["rewards"]:
            raise ValueError(f"Reward {reward_id} not found")
        name = self._data["rewards"][reward_id]["name"]
        del self._data["rewards"][reward_id]
        # Clean up pending requests for this reward
        to_remove = [
            rid
            for rid, req in self._data["pending_requests"].items()
            if req["reward_id"] == reward_id
        ]
        for rid in to_remove:
            del self._data["pending_requests"][rid]
        await self._async_save()
        _LOGGER.info("Removed reward %s (%s)", name, reward_id)

    async def async_update_reward(
        self, reward_id: str, **kwargs: Any
    ) -> None:
        """Update reward fields (name, cost, icon, automation_id)."""
        if reward_id not in self._data["rewards"]:
            raise ValueError(f"Reward {reward_id} not found")
        valid_keys = {"name", "cost", "icon", "automation_id"}
        for key, value in kwargs.items():
            if key not in valid_keys:
                raise ValueError(f"Invalid reward field: {key}")
            if key == "cost" and value <= 0:
                raise ValueError("Cost must be positive")
            self._data["rewards"][reward_id][key] = value
        await self._async_save()

    # --- Redemption Requests ---

    @property
    def pending_requests(self) -> dict[str, dict[str, Any]]:
        """Return all pending requests."""
        return self._data["pending_requests"]

    async def async_request_redemption(
        self, child_id: str, reward_id: str
    ) -> str:
        """Create a pending redemption request. Deducts stickers immediately. Returns request ID."""
        if child_id not in self._data["children"]:
            raise ValueError(f"Child {child_id} not found")
        if reward_id not in self._data["rewards"]:
            raise ValueError(f"Reward {reward_id} not found")
        reward = self._data["rewards"][reward_id]
        child = self._data["children"][child_id]
        if child["stickers"] < reward["cost"]:
            raise ValueError(
                f"Not enough stickers. Need {reward['cost']}, have {child['stickers']}"
            )
        # Check for duplicate pending request
        for req in self._data["pending_requests"].values():
            if req["child_id"] == child_id and req["reward_id"] == reward_id:
                raise ValueError(
                    f"Already have a pending request for this reward"
                )

        # Deduct stickers immediately on request
        child["stickers"] -= reward["cost"]

        request_id = _new_id()
        self._data["pending_requests"][request_id] = {
            "child_id": child_id,
            "reward_id": reward_id,
            "cost_deducted": reward["cost"],
            "timestamp": _now_iso(),
        }

        # Record history
        self._data["history"].append(
            {
                "type": "redeem",
                "child_id": child_id,
                "reward_id": reward_id,
                "amount": reward["cost"],
                "reward_name": reward["name"],
                "timestamp": _now_iso(),
            }
        )

        await self._async_save()
        return request_id

    async def async_approve_redemption(self, request_id: str) -> dict[str, Any]:
        """Approve a redemption. Stickers already deducted on request. Returns request details."""
        if request_id not in self._data["pending_requests"]:
            raise ValueError(f"Request {request_id} not found")
        request = self._data["pending_requests"][request_id]
        child_id = request["child_id"]
        reward_id = request["reward_id"]

        if child_id not in self._data["children"]:
            raise ValueError(f"Child {child_id} no longer exists")
        if reward_id not in self._data["rewards"]:
            raise ValueError(f"Reward {reward_id} no longer exists")

        reward = self._data["rewards"][reward_id]
        child = self._data["children"][child_id]

        # Remove the pending request (stickers already deducted)
        del self._data["pending_requests"][request_id]
        await self._async_save()

        return {
            "child_id": child_id,
            "child_name": child["name"],
            "reward_id": reward_id,
            "reward_name": reward["name"],
            "reward_cost": request.get("cost_deducted", reward["cost"]),
            "automation_id": reward.get("automation_id"),
            "new_balance": child["stickers"],
        }

    async def async_deny_redemption(self, request_id: str) -> dict[str, Any]:
        """Deny a redemption. Refunds the deducted stickers. Returns request details."""
        if request_id not in self._data["pending_requests"]:
            raise ValueError(f"Request {request_id} not found")
        request = self._data["pending_requests"][request_id]
        child_id = request["child_id"]
        reward_id = request["reward_id"]
        cost_deducted = request.get("cost_deducted", 0)

        child_name = self._data["children"].get(child_id, {}).get("name", "Unknown")
        reward_name = self._data["rewards"].get(reward_id, {}).get("name", "Unknown")

        # Refund stickers
        if child_id in self._data["children"] and cost_deducted > 0:
            self._data["children"][child_id]["stickers"] += cost_deducted
            self._data["history"].append(
                {
                    "type": "refund",
                    "child_id": child_id,
                    "reward_id": reward_id,
                    "amount": cost_deducted,
                    "reward_name": reward_name,
                    "reason": "Redemption denied",
                    "timestamp": _now_iso(),
                }
            )

        new_balance = self._data["children"].get(child_id, {}).get("stickers", 0)

        del self._data["pending_requests"][request_id]
        await self._async_save()

        return {
            "child_id": child_id,
            "child_name": child_name,
            "reward_id": reward_id,
            "reward_name": reward_name,
            "refunded": cost_deducted,
            "new_balance": new_balance,
        }

    def get_pending_requests_for_child(self, child_id: str) -> list[dict[str, Any]]:
        """Get all pending requests for a child."""
        results = []
        for request_id, request in self._data["pending_requests"].items():
            if request["child_id"] == child_id:
                reward = self._data["rewards"].get(request["reward_id"], {})
                results.append(
                    {
                        "request_id": request_id,
                        "reward_id": request["reward_id"],
                        "reward_name": reward.get("name", "Unknown"),
                        "reward_cost": reward.get("cost", 0),
                        "timestamp": request["timestamp"],
                    }
                )
        return results

    # --- History ---

    @property
    def history(self) -> list[dict[str, Any]]:
        """Return full history."""
        return self._data["history"]

    def get_child_history(
        self, child_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get recent history for a child."""
        child_history = [
            entry
            for entry in self._data["history"]
            if entry.get("child_id") == child_id
        ]
        return child_history[-limit:]

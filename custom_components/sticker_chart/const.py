"""Constants for the Sticker Chart integration."""

DOMAIN = "sticker_chart"
STORAGE_KEY = "sticker_chart"
STORAGE_VERSION = 1

# Events fired by the integration
EVENT_REDEMPTION_REQUESTED = f"{DOMAIN}_redemption_requested"
EVENT_REDEMPTION_APPROVED = f"{DOMAIN}_redemption_approved"
EVENT_REDEMPTION_DENIED = f"{DOMAIN}_redemption_denied"
EVENT_STICKERS_GRANTED = f"{DOMAIN}_stickers_granted"
EVENT_STICKERS_REVOKED = f"{DOMAIN}_stickers_revoked"

# Service names
SERVICE_ADD_CHILD = "add_child"
SERVICE_REMOVE_CHILD = "remove_child"
SERVICE_GRANT_STICKERS = "grant_stickers"
SERVICE_REVOKE_STICKERS = "revoke_stickers"
SERVICE_ADD_REWARD = "add_reward"
SERVICE_REMOVE_REWARD = "remove_reward"
SERVICE_UPDATE_REWARD = "update_reward"
SERVICE_REQUEST_REDEMPTION = "request_redemption"
SERVICE_APPROVE_REDEMPTION = "approve_redemption"
SERVICE_DENY_REDEMPTION = "deny_redemption"

# Attributes
ATTR_CHILD_ID = "child_id"
ATTR_CHILD_NAME = "child_name"
ATTR_AMOUNT = "amount"
ATTR_REASON = "reason"
ATTR_REWARD_ID = "reward_id"
ATTR_REWARD_NAME = "reward_name"
ATTR_REWARD_COST = "cost"
ATTR_REWARD_ICON = "icon"
ATTR_AUTOMATION_ID = "automation_id"
ATTR_REQUEST_ID = "request_id"

PLATFORMS = ["sensor", "button"]

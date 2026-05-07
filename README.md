# Sticker Chart for Home Assistant

A custom Home Assistant integration for managing kids' sticker reward charts. Track sticker balances, configure rewards, and handle redemption approvals with parent notifications.

## Features

- **Per-child sticker tracking** with balance sensors and history
- **Reward catalog** shared across all children with configurable sticker costs
- **Redemption approval workflow** — kids request rewards, parents approve or deny via notifications
- **Automation triggers** — approved rewards can fire HA automations (unblock internet, unlock screen time, etc.)
- **Per-child dashboards** — each child only sees their own balance and rewards
- **Admin management** via HA's options flow UI or service calls
- **HACS compatible** for easy installation

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `TheOutdoorProgrammer/ha-sticker-chart` as an **Integration**
4. Install "Sticker Chart"
5. Restart Home Assistant

### Manual

1. Copy `custom_components/sticker_chart/` to your `config/custom_components/` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "Sticker Chart" and add it
3. Use the integration's **Configure** button (options flow) to add children and rewards

## Managing Children and Rewards

### Via the Options Flow (UI)

Click **Configure** on the Sticker Chart integration to:
- Add/remove children
- Add/remove/update rewards (name, cost, icon, automation ID)

### Via Services

All management is also available through HA services (Developer Tools → Services):

| Service | Description |
|---------|-------------|
| `sticker_chart.add_child` | Add a new child |
| `sticker_chart.remove_child` | Remove a child |
| `sticker_chart.grant_stickers` | Award stickers to a child |
| `sticker_chart.revoke_stickers` | Remove stickers from a child |
| `sticker_chart.add_reward` | Add a reward to the catalog |
| `sticker_chart.remove_reward` | Remove a reward |
| `sticker_chart.update_reward` | Update reward properties |
| `sticker_chart.request_redemption` | Request to redeem a reward (creates pending request) |
| `sticker_chart.approve_redemption` | Approve a pending request (deducts stickers) |
| `sticker_chart.deny_redemption` | Deny a pending request (stickers untouched) |

## Entities Created

For each child, the integration creates:

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.sticker_chart_{child}_balance` | Sensor | Current sticker count |
| `sensor.sticker_chart_{child}_pending` | Sensor | Number of pending redemption requests |
| `button.sticker_chart_{child}_{reward}_redeem` | Button | Request a reward (disabled when balance is too low or request already pending) |

All entities are grouped under a device per child (e.g., "Alice's Sticker Chart").

## Events

The integration fires events that you use to build your own automations:

| Event | When | Data |
|-------|------|------|
| `sticker_chart_redemption_requested` | Kid presses a reward button | `request_id`, `child_id`, `child_name`, `reward_id`, `reward_name`, `reward_cost`, `automation_id` |
| `sticker_chart_redemption_approved` | Parent approves a request | `child_id`, `child_name`, `reward_id`, `reward_name`, `reward_cost`, `automation_id`, `new_balance` |
| `sticker_chart_redemption_denied` | Parent denies a request | `child_id`, `child_name`, `reward_id`, `reward_name` |
| `sticker_chart_stickers_granted` | Stickers given to a child | `child_id`, `child_name`, `amount`, `reason`, `new_balance` |
| `sticker_chart_stickers_revoked` | Stickers taken from a child | `child_id`, `child_name`, `amount`, `reason`, `new_balance` |

## Example Automations

### Notify Parents When a Child Requests a Reward

This sends an actionable notification to both parents when any child requests a reward. Tapping "Approve" or "Deny" on the notification calls the appropriate service.

```yaml
alias: "Sticker Chart - Reward Request Notification"
trigger:
  - platform: event
    event_type: sticker_chart_redemption_requested
action:
  - service: notify.mobile_app_moms_phone
    data:
      title: "Sticker Chart Request"
      message: >
        {{ trigger.event.data.child_name }} wants to redeem
        "{{ trigger.event.data.reward_name }}"
        for {{ trigger.event.data.reward_cost }} stickers!
      data:
        actions:
          - action: "APPROVE_{{ trigger.event.data.request_id }}"
            title: "Approve"
          - action: "DENY_{{ trigger.event.data.request_id }}"
            title: "Deny"
  - service: notify.mobile_app_dads_phone
    data:
      title: "Sticker Chart Request"
      message: >
        {{ trigger.event.data.child_name }} wants to redeem
        "{{ trigger.event.data.reward_name }}"
        for {{ trigger.event.data.reward_cost }} stickers!
      data:
        actions:
          - action: "APPROVE_{{ trigger.event.data.request_id }}"
            title: "Approve"
          - action: "DENY_{{ trigger.event.data.request_id }}"
            title: "Deny"
mode: parallel
```

### Handle Notification Responses

```yaml
alias: "Sticker Chart - Handle Approval Response"
trigger:
  - platform: event
    event_type: mobile_app_notification_action
action:
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ trigger.event.data.action.startswith('APPROVE_') }}"
        sequence:
          - service: sticker_chart.approve_redemption
            data:
              request_id: "{{ trigger.event.data.action.replace('APPROVE_', '') }}"
      - conditions:
          - condition: template
            value_template: "{{ trigger.event.data.action.startswith('DENY_') }}"
        sequence:
          - service: sticker_chart.deny_redemption
            data:
              request_id: "{{ trigger.event.data.action.replace('DENY_', '') }}"
mode: parallel
```

### Run Automation on Approved Reward

When a reward with an `automation_id` is approved, trigger that automation:

```yaml
alias: "Sticker Chart - Execute Reward Automation"
trigger:
  - platform: event
    event_type: sticker_chart_redemption_approved
condition:
  - condition: template
    value_template: "{{ trigger.event.data.automation_id is not none }}"
action:
  - service: automation.trigger
    target:
      entity_id: "{{ trigger.event.data.automation_id }}"
mode: parallel
```

### Example: Screen Time Reward Automation

Create this automation, then set its entity ID as the `automation_id` when adding a "Screen Time" reward:

```yaml
alias: "Grant Extra Screen Time"
trigger: []  # Only triggered by sticker chart
action:
  - service: switch.turn_on
    target:
      entity_id: switch.kids_internet_access
  - delay:
      hours: 1
  - service: switch.turn_off
    target:
      entity_id: switch.kids_internet_access
mode: restart
```

## Per-Child Dashboard Setup

To isolate each child's view:

1. **Create HA user accounts** for each child (Settings → People → Users)
2. **Create a dashboard** per child (Settings → Dashboards → Add Dashboard)
3. **Restrict dashboard visibility** to that child's user account
4. On each child's dashboard, add:
   - A **sensor card** showing their balance sensor (`sensor.sticker_chart_{child}_balance`)
   - **Button cards** for each reward (`button.sticker_chart_{child}_{reward}_redeem`)
5. Create a separate **Admin dashboard** visible only to parent accounts with:
   - All children's balance sensors
   - Service call buttons for granting/revoking stickers
   - A pending requests overview

## Admin Dashboard Tips

For the parent admin dashboard, consider using:

- **Entities card** — Show all children's balance sensors at a glance
- **Button cards with service calls** — Quick +1/+5/+10 sticker buttons per child
- **Markdown card** — Display pending requests from sensor attributes
- **Conditional cards** — Show/hide approval buttons based on pending request count

## Data Storage

All data is stored in `.storage/sticker_chart` in your HA config directory. This file is included in Home Assistant backups automatically.

## Contributing

Issues and PRs welcome at [GitHub](https://github.com/TheOutdoorProgrammer/ha-sticker-chart).

## License

MIT

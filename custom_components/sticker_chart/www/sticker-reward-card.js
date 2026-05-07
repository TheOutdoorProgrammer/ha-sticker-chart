class StickerRewardCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._config) return;
    this._render();
  }

  setConfig(config) {
    if (!config.entity) throw new Error("You need to define an entity");
    this._config = config;
  }

  getCardSize() {
    return 3;
  }

  static getStubConfig() {
    return { entity: "" };
  }

  _render() {
    const entityId = this._config.entity;
    const state = this._hass.states[entityId];
    if (!state) {
      this.innerHTML = `<ha-card><div style="padding:16px">Entity not found: ${entityId}</div></ha-card>`;
      return;
    }

    const attrs = state.attributes;
    const rewardName = attrs.reward_name || "Reward";
    const cost = attrs.reward_cost || 0;
    const balance = attrs.current_balance || 0;
    const canAfford = attrs.can_afford || false;
    const hasPending = attrs.has_pending || false;
    const status = attrs.status || "";
    const icon = attrs.icon || this._config.icon || "mdi:star";
    const progress = cost > 0 ? Math.min(balance / cost, 1) : 0;
    const progressPct = Math.round(progress * 100);

    let cardClass, statusIcon, statusText, bgGradient, iconColor, glowStyle;

    if (hasPending) {
      cardClass = "pending";
      statusIcon = "⏳";
      statusText = "Waiting for Mom & Dad...";
      bgGradient = "linear-gradient(135deg, #ff9800 0%, #ff5722 100%)";
      iconColor = "#fff";
      glowStyle = "0 0 20px rgba(255,152,0,0.4)";
    } else if (canAfford) {
      cardClass = "ready";
      statusIcon = "🎉";
      statusText = "Tap to redeem!";
      bgGradient = "linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)";
      iconColor = "#fff";
      glowStyle = "0 0 25px rgba(76,175,80,0.6)";
    } else {
      cardClass = "locked";
      statusIcon = "🔒";
      statusText = status;
      bgGradient = "linear-gradient(135deg, #455a64 0%, #263238 100%)";
      iconColor = "#78909c";
      glowStyle = "none";
    }

    const progressColor = hasPending
      ? "#ffcc02"
      : canAfford
        ? "#a5d6a7"
        : "#42a5f5";

    this.innerHTML = `
      <ha-card class="sticker-reward ${cardClass}" style="
        background: ${bgGradient};
        border-radius: 20px;
        overflow: hidden;
        cursor: ${canAfford && !hasPending ? "pointer" : "default"};
        box-shadow: ${glowStyle};
        transition: all 0.3s ease;
        position: relative;
      ">
        ${hasPending ? '<div class="pulse-overlay"></div>' : ""}
        ${canAfford && !hasPending ? '<div class="shimmer"></div>' : ""}

        <div style="padding: 20px; position: relative; z-index: 1;">
          <!-- Icon + Name -->
          <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 16px;">
            <div style="
              width: 56px; height: 56px;
              border-radius: 16px;
              background: rgba(255,255,255,0.15);
              display: flex; align-items: center; justify-content: center;
              font-size: 28px;
              backdrop-filter: blur(10px);
            ">
              <ha-icon icon="${icon}" style="color: ${iconColor}; --mdc-icon-size: 32px;"></ha-icon>
            </div>
            <div style="flex: 1; min-width: 0;">
              <div style="
                font-size: 18px; font-weight: 700; color: #fff;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
              ">${rewardName}</div>
              <div style="font-size: 13px; color: rgba(255,255,255,0.7); margin-top: 2px;">
                ${cost} ⭐ needed
              </div>
            </div>
          </div>

          <!-- Progress Bar -->
          <div style="margin-bottom: 14px;">
            <div style="
              display: flex; justify-content: space-between; align-items: center;
              margin-bottom: 6px;
            ">
              <span style="font-size: 12px; color: rgba(255,255,255,0.6); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                Progress
              </span>
              <span style="font-size: 13px; color: #fff; font-weight: 700;">
                ${balance} / ${cost}
              </span>
            </div>
            <div style="
              height: 12px; background: rgba(0,0,0,0.3); border-radius: 6px;
              overflow: hidden; position: relative;
            ">
              <div style="
                height: 100%; width: ${progressPct}%;
                background: ${progressColor};
                border-radius: 6px;
                transition: width 0.5s ease;
                ${canAfford ? "animation: progressGlow 2s ease-in-out infinite;" : ""}
              "></div>
            </div>
          </div>

          <!-- Status -->
          <div style="
            text-align: center; padding: 10px 16px;
            background: rgba(0,0,0,0.2); border-radius: 12px;
            font-size: 15px; font-weight: 600; color: #fff;
            ${canAfford && !hasPending ? "animation: bounce 2s ease-in-out infinite;" : ""}
          ">
            ${statusIcon} ${statusText}
          </div>
        </div>
      </ha-card>

      <style>
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-3px); }
        }
        @keyframes progressGlow {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
        @keyframes pulse {
          0%, 100% { opacity: 0; }
          50% { opacity: 0.15; }
        }
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .sticker-reward.ready:active {
          transform: scale(0.97);
        }
        .pulse-overlay {
          position: absolute; top: 0; left: 0; right: 0; bottom: 0;
          background: rgba(255,255,255,1);
          animation: pulse 2s ease-in-out infinite;
          pointer-events: none;
          z-index: 0;
        }
        .shimmer {
          position: absolute; top: 0; left: 0; right: 0; bottom: 0;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
          animation: shimmer 3s ease-in-out infinite;
          pointer-events: none;
          z-index: 0;
        }
      </style>
    `;

    // Click handler
    if (canAfford && !hasPending) {
      this.querySelector("ha-card").addEventListener("click", () => {
        this._hass.callService("button", "press", {
          entity_id: entityId,
        });
      });
    }
  }
}

customElements.define("sticker-reward-card", StickerRewardCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "sticker-reward-card",
  name: "Sticker Reward Card",
  description: "A fun, colorful reward card for the Sticker Chart integration",
  preview: true,
});

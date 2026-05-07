// ── Sticker Reward Card ──────────────────────────────────────────────────────

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
          pointer-events: none; z-index: 0;
        }
        .shimmer {
          position: absolute; top: 0; left: 0; right: 0; bottom: 0;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
          animation: shimmer 3s ease-in-out infinite;
          pointer-events: none; z-index: 0;
        }
      </style>
    `;

    if (canAfford && !hasPending) {
      this.querySelector("ha-card").addEventListener("click", () => {
        this._hass.callService("button", "press", { entity_id: entityId });
      });
    }
  }
}

customElements.define("sticker-reward-card", StickerRewardCard);

// ── Sticker Balance Card ────────────────────────────────────────────────────

class StickerBalanceCard extends HTMLElement {
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
    return 2;
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

    const balance = parseInt(state.state) || 0;
    const name = state.attributes.child_name || "Kid";

    // Generate star field — more stars for higher balances
    const starCount = Math.min(balance, 30);
    let starsHtml = "";
    for (let i = 0; i < starCount; i++) {
      const left = Math.random() * 90 + 5;
      const top = Math.random() * 70 + 15;
      const size = Math.random() * 10 + 8;
      const delay = Math.random() * 3;
      const dur = 2 + Math.random() * 2;
      starsHtml += `<div style="
        position: absolute; left: ${left}%; top: ${top}%;
        font-size: ${size}px; opacity: 0.4;
        animation: twinkle ${dur}s ease-in-out ${delay}s infinite;
        pointer-events: none;
      ">⭐</div>`;
    }

    // Color shifts based on balance thresholds
    let bgGradient, glowColor;
    if (balance >= 20) {
      bgGradient = "linear-gradient(135deg, #f9a825 0%, #ff8f00 50%, #e65100 100%)";
      glowColor = "rgba(255,143,0,0.5)";
    } else if (balance >= 10) {
      bgGradient = "linear-gradient(135deg, #7c4dff 0%, #536dfe 50%, #448aff 100%)";
      glowColor = "rgba(83,109,254,0.4)";
    } else if (balance >= 5) {
      bgGradient = "linear-gradient(135deg, #26c6da 0%, #00acc1 50%, #0097a7 100%)";
      glowColor = "rgba(0,172,193,0.3)";
    } else {
      bgGradient = "linear-gradient(135deg, #78909c 0%, #546e7a 50%, #455a64 100%)";
      glowColor = "none";
    }

    this.innerHTML = `
      <ha-card style="
        background: ${bgGradient};
        border-radius: 20px;
        overflow: hidden;
        position: relative;
        box-shadow: ${glowColor !== "none" ? "0 0 30px " + glowColor : "none"};
      ">
        ${starsHtml}

        <div style="padding: 24px; position: relative; z-index: 1; text-align: center;">
          <div style="font-size: 14px; color: rgba(255,255,255,0.7); font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
            ${name}'s Stickers
          </div>

          <div style="
            font-size: 64px; font-weight: 800; color: #fff;
            line-height: 1; margin-bottom: 4px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
            ${balance > 0 ? "animation: countPulse 3s ease-in-out infinite;" : ""}
          ">
            ${balance}
          </div>

          <div style="font-size: 18px; color: rgba(255,255,255,0.8);">
            ⭐ sticker${balance !== 1 ? "s" : ""}
          </div>
        </div>
      </ha-card>

      <style>
        @keyframes twinkle {
          0%, 100% { opacity: 0.2; transform: scale(1); }
          50% { opacity: 0.7; transform: scale(1.2); }
        }
        @keyframes countPulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.03); }
        }
      </style>
    `;
  }
}

customElements.define("sticker-balance-card", StickerBalanceCard);

// ── Sticker Pending Card ────────────────────────────────────────────────────

class StickerPendingCard extends HTMLElement {
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
    return 2;
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

    const pending = state.attributes.pending_requests || [];
    const count = pending.length;

    if (count === 0) {
      this.innerHTML = `
        <ha-card style="
          background: linear-gradient(135deg, #37474f 0%, #263238 100%);
          border-radius: 20px; overflow: hidden;
        ">
          <div style="padding: 20px; text-align: center;">
            <div style="font-size: 36px; margin-bottom: 8px; opacity: 0.5;">😴</div>
            <div style="font-size: 14px; color: rgba(255,255,255,0.4); font-weight: 600;">
              No pending requests
            </div>
          </div>
        </ha-card>
      `;
      return;
    }

    let requestsHtml = "";
    for (const req of pending) {
      const name = req.reward_name || "Unknown";
      const cost = req.reward_cost || 0;
      requestsHtml += `
        <div style="
          display: flex; align-items: center; gap: 12px;
          padding: 12px 16px; background: rgba(255,255,255,0.1);
          border-radius: 12px; margin-bottom: 8px;
        ">
          <div style="font-size: 24px; animation: pendingSpin 3s linear infinite;">⏳</div>
          <div style="flex: 1; min-width: 0;">
            <div style="font-size: 15px; font-weight: 700; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
              ${name}
            </div>
            <div style="font-size: 12px; color: rgba(255,255,255,0.6);">
              ${cost} ⭐ will be deducted if approved
            </div>
          </div>
        </div>
      `;
    }

    this.innerHTML = `
      <ha-card style="
        background: linear-gradient(135deg, #e65100 0%, #bf360c 100%);
        border-radius: 20px; overflow: hidden; position: relative;
      ">
        <div class="pending-pulse-bg"></div>

        <div style="padding: 20px; position: relative; z-index: 1;">
          <div style="
            display: flex; align-items: center; gap: 10px;
            margin-bottom: 14px;
          ">
            <div style="
              width: 36px; height: 36px; border-radius: 50%;
              background: rgba(255,255,255,0.2);
              display: flex; align-items: center; justify-content: center;
              font-size: 18px; font-weight: 800; color: #fff;
            ">${count}</div>
            <div style="font-size: 14px; color: rgba(255,255,255,0.8); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
              Pending Request${count !== 1 ? "s" : ""}
            </div>
          </div>

          ${requestsHtml}

          <div style="
            text-align: center; margin-top: 4px;
            font-size: 13px; color: rgba(255,255,255,0.5); font-style: italic;
          ">
            Waiting for Mom or Dad to review...
          </div>
        </div>
      </ha-card>

      <style>
        @keyframes pendingSpin {
          0% { transform: rotate(0deg); }
          25% { transform: rotate(15deg); }
          75% { transform: rotate(-15deg); }
          100% { transform: rotate(0deg); }
        }
        .pending-pulse-bg {
          position: absolute; top: 0; left: 0; right: 0; bottom: 0;
          background: rgba(255,255,255,1);
          animation: pendingPulse 2.5s ease-in-out infinite;
          pointer-events: none; z-index: 0;
        }
        @keyframes pendingPulse {
          0%, 100% { opacity: 0; }
          50% { opacity: 0.08; }
        }
      </style>
    `;
  }
}

customElements.define("sticker-pending-card", StickerPendingCard);

// ── Card Registration ───────────────────────────────────────────────────────

window.customCards = window.customCards || [];
window.customCards.push(
  {
    type: "sticker-reward-card",
    name: "Sticker Reward Card",
    description: "A fun, colorful reward card for the Sticker Chart integration",
    preview: true,
  },
  {
    type: "sticker-balance-card",
    name: "Sticker Balance Card",
    description: "Shows a child's sticker balance with animated stars and color tiers",
    preview: true,
  },
  {
    type: "sticker-pending-card",
    name: "Sticker Pending Card",
    description: "Shows pending reward redemption requests waiting for parent approval",
    preview: true,
  },
);

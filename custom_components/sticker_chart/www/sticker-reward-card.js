// ── Sticker Reward Card ──────────────────────────────────────────────────────

class StickerRewardCard extends HTMLElement {
  constructor() {
    super();
    this._optimisticPending = false;
    this._lastState = null;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config) return;

    const state = hass.states[this._config.entity];
    if (!state) return;

    // If server confirms pending, clear the optimistic flag
    if (state.attributes.has_pending) {
      this._optimisticPending = false;
    }

    // Dirty check — only re-render when data actually changes
    const key = `${state.state}|${state.attributes.current_balance}|${state.attributes.can_afford}|${state.attributes.has_pending}|${state.attributes.description || ""}|${this._optimisticPending}`;
    if (key === this._lastState) return;
    this._lastState = key;

    this._render();
  }

  setConfig(config) {
    if (!config.entity) throw new Error("You need to define an entity");
    this._config = config;
  }

  getCardSize() { return 3; }
  static getStubConfig() { return { entity: "" }; }

  _showCostAnimation(cost) {
    const floater = document.createElement("div");
    floater.textContent = `-${cost} ⭐`;
    floater.style.cssText = `
      position: absolute; top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      font-size: 32px; font-weight: 800; color: #fff;
      text-shadow: 0 2px 8px rgba(0,0,0,0.5);
      pointer-events: none; z-index: 10;
      animation: sc-floatUp 1.5s ease-out forwards;
    `;
    const card = this.querySelector("ha-card");
    if (card) {
      card.appendChild(floater);
      setTimeout(() => floater.remove(), 1500);
    }
  }

  _render() {
    const state = this._hass.states[this._config.entity];
    if (!state) {
      this.innerHTML = `<ha-card><div style="padding:16px">Entity not found</div></ha-card>`;
      return;
    }

    const attrs = state.attributes;
    const rewardName = attrs.reward_name || "Reward";
    const cost = attrs.reward_cost || 0;
    const balance = attrs.current_balance || 0;
    const canAfford = attrs.can_afford || false;
    const serverPending = attrs.has_pending || false;
    const hasPending = serverPending || this._optimisticPending;
    const status = attrs.status || "";
    const description = attrs.description || "";
    const icon = attrs.icon || this._config.icon || "mdi:star";
    const progressPct = cost > 0 ? Math.round(Math.min(balance / cost, 1) * 100) : 0;
    const isRedeemable = canAfford && !hasPending;

    let statusIcon, statusText, bg, iconColor;

    if (hasPending) {
      statusIcon = "⏳"; statusText = "Waiting for Mom & Dad...";
      bg = "linear-gradient(135deg, #ff9800 0%, #ff5722 100%)";
      iconColor = "#fff";
    } else if (canAfford) {
      statusIcon = "🎉"; statusText = "Tap to redeem!";
      bg = "linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)";
      iconColor = "#fff";
    } else {
      statusIcon = "🔒"; statusText = status;
      bg = "linear-gradient(135deg, #455a64 0%, #263238 100%)";
      iconColor = "#78909c";
    }

    const progressColor = hasPending ? "#ffcc02" : canAfford ? "#a5d6a7" : "#42a5f5";
    const entityId = this._config.entity;

    this.innerHTML = `
      <ha-card style="background:${bg};border-radius:20px;overflow:hidden;
        cursor:${isRedeemable ? "pointer" : "default"};
        transition:background 0.4s ease;position:relative;">

        <div style="padding:20px;position:relative;z-index:1;">
          <div style="display:flex;align-items:center;gap:14px;margin-bottom:16px;">
            <div style="width:56px;height:56px;border-radius:16px;background:rgba(255,255,255,0.15);
              display:flex;align-items:center;justify-content:center;">
              <ha-icon icon="${icon}" style="color:${iconColor};--mdc-icon-size:32px;"></ha-icon>
            </div>
            <div style="flex:1;min-width:0;">
              <div style="font-size:18px;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                ${rewardName}
              </div>
              <div style="font-size:13px;color:rgba(255,255,255,0.7);margin-top:2px;">
                ${cost} ⭐ needed
              </div>
              ${description ? `<div style="font-size:12px;color:rgba(255,255,255,0.5);margin-top:4px;font-style:italic;">${description}</div>` : ""}
            </div>
          </div>

          <div style="margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
              <span style="font-size:12px;color:rgba(255,255,255,0.6);font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Progress</span>
              <span style="font-size:13px;color:#fff;font-weight:700;">${balance} / ${cost}</span>
            </div>
            <div style="height:12px;background:rgba(0,0,0,0.3);border-radius:6px;overflow:hidden;">
              <div style="height:100%;width:${progressPct}%;background:${progressColor};border-radius:6px;transition:width 0.5s ease;"></div>
            </div>
          </div>

          <div style="text-align:center;padding:10px 16px;background:rgba(0,0,0,0.2);border-radius:12px;font-size:15px;font-weight:600;color:#fff;">
            ${statusIcon} ${statusText}
          </div>
        </div>
      </ha-card>

      <style>
        @keyframes sc-floatUp {
          0% { opacity:1; transform:translate(-50%,-50%) scale(1); }
          30% { opacity:1; transform:translate(-50%,-80%) scale(1.3); }
          100% { opacity:0; transform:translate(-50%,-180%) scale(0.8); }
        }
      </style>
    `;

    if (isRedeemable) {
      this.querySelector("ha-card").addEventListener("click", () => {
        if (this._optimisticPending) return;
        this._optimisticPending = true;
        this._showCostAnimation(cost);
        this._hass.callService("button", "press", { entity_id: entityId });
        this._lastState = null; // force re-render
        setTimeout(() => this._render(), 300);
      });
    }
  }
}

customElements.define("sticker-reward-card", StickerRewardCard);

// ── Sticker Balance Card ────────────────────────────────────────────────────

class StickerBalanceCard extends HTMLElement {
  constructor() {
    super();
    this._lastState = null;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config) return;

    const state = hass.states[this._config.entity];
    if (!state) return;

    const key = state.state;
    if (key === this._lastState) return;
    this._lastState = key;

    this._render();
  }

  setConfig(config) {
    if (!config.entity) throw new Error("You need to define an entity");
    this._config = config;
  }

  getCardSize() { return 2; }
  static getStubConfig() { return { entity: "" }; }

  _render() {
    const state = this._hass.states[this._config.entity];
    if (!state) {
      this.innerHTML = `<ha-card><div style="padding:16px">Entity not found</div></ha-card>`;
      return;
    }

    const balance = parseInt(state.state) || 0;
    const name = state.attributes.child_name || "Kid";

    // Deterministic stars — no animations, just static sparkle
    const starCount = Math.min(balance, 20);
    let starsHtml = "";
    for (let i = 0; i < starCount; i++) {
      const seed = i * 7919;
      const left = ((seed * 13) % 85) + 5;
      const top = ((seed * 17) % 60) + 18;
      const size = (seed % 8) + 8;
      const opacity = 0.15 + (seed % 20) / 100;
      starsHtml += `<div style="position:absolute;left:${left}%;top:${top}%;font-size:${size}px;opacity:${opacity};pointer-events:none;">⭐</div>`;
    }

    let bg;
    if (balance >= 20) {
      bg = "linear-gradient(135deg, #f9a825 0%, #ff8f00 50%, #e65100 100%)";
    } else if (balance >= 10) {
      bg = "linear-gradient(135deg, #7c4dff 0%, #536dfe 50%, #448aff 100%)";
    } else if (balance >= 5) {
      bg = "linear-gradient(135deg, #26c6da 0%, #00acc1 50%, #0097a7 100%)";
    } else {
      bg = "linear-gradient(135deg, #78909c 0%, #546e7a 50%, #455a64 100%)";
    }

    this.innerHTML = `
      <ha-card style="background:${bg};border-radius:20px;overflow:hidden;position:relative;">
        ${starsHtml}
        <div style="padding:24px;position:relative;z-index:1;text-align:center;">
          <div style="font-size:14px;color:rgba(255,255,255,0.7);font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
            ${name}'s Stickers
          </div>
          <div style="font-size:64px;font-weight:800;color:#fff;line-height:1;margin-bottom:4px;text-shadow:0 2px 10px rgba(0,0,0,0.3);">
            ${balance}
          </div>
          <div style="font-size:18px;color:rgba(255,255,255,0.8);">
            ⭐ sticker${balance !== 1 ? "s" : ""}
          </div>
        </div>
      </ha-card>
    `;
  }
}

customElements.define("sticker-balance-card", StickerBalanceCard);

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
    description: "Shows a child's sticker balance with color tiers",
    preview: true,
  },
);

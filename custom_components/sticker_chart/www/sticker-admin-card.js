// ── Sticker Admin Reward Manager Card ────────────────────────────────────────

class StickerAdminRewardsCard extends HTMLElement {
  constructor() {
    super();
    this._lastKey = null;
    this._editingId = null;
    this._showAddForm = false;
    this._built = false;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config) return;
    if (this._editingId || this._showAddForm) return;
    const rewards = this._getRewards();
    const key = JSON.stringify(rewards);
    if (key === this._lastKey) return;
    this._lastKey = key;
    this._fullRender(rewards);
  }

  setConfig(config) { this._config = config; }
  getCardSize() { return 4; }
  static getStubConfig() { return {}; }

  _getRewards() {
    const seen = new Set();
    const rewards = [];
    for (const [eid, state] of Object.entries(this._hass.states)) {
      if (!eid.startsWith("button.") || !state.attributes.reward_id) continue;
      if (!state.attributes.child_id) continue;
      const rid = state.attributes.reward_id;
      if (seen.has(rid)) continue;
      seen.add(rid);
      rewards.push({
        reward_id: rid,
        name: state.attributes.reward_name || "",
        cost: state.attributes.reward_cost || 0,
        description: state.attributes.description || "",
        icon: state.attributes.icon || "mdi:star",
        automation_id: state.attributes.automation_id || "",
      });
    }
    return rewards;
  }

  _resetFormState() {
    this._editingId = null;
    this._showAddForm = false;
    this._lastKey = null;
  }

  // After a service call, wait then force refresh
  _refreshAfterAction(delay = 800) {
    this._resetFormState();
    setTimeout(() => {
      this._lastKey = null;
      this._fullRender(this._getRewards());
    }, delay);
  }

  _fullRender(rewards) {
    let rowsHtml = "";
    for (const r of rewards) {
      const autoHtml = r.automation_id
        ? `<div class="sc-auto sc-auto-link" data-auto="${r.automation_id}">⚡ ${r.automation_id}</div>`
        : `<div class="sc-auto-none">No automation</div>`;
      rowsHtml += `
        <div class="sc-row">
          <div class="sc-icon-box"><ha-icon icon="${r.icon}" style="--mdc-icon-size:24px;"></ha-icon></div>
          <div class="sc-info">
            <div class="sc-name">${r.name}</div>
            <div class="sc-meta">${r.cost} ⭐ ${r.description ? `· <em>${r.description}</em>` : ""}</div>
            ${autoHtml}
          </div>
          <div class="sc-actions">
            <button class="sc-btn sc-btn-edit sc-edit-btn" data-id="${r.reward_id}">Edit</button>
            <button class="sc-btn sc-btn-del sc-del-btn" data-id="${r.reward_id}" data-name="${r.name}">✕</button>
          </div>
        </div>`;
    }

    this.innerHTML = `
      <ha-card>
        <div class="sc-wrap">
          <div class="sc-header">
            <div class="sc-title">Reward Catalog</div>
            <button class="sc-btn sc-btn-add sc-toggle-add">+ Add Reward</button>
          </div>
          <div class="sc-list">${rowsHtml}</div>
          <div class="sc-form-container"></div>
        </div>
      </ha-card>
      <style>${this._styles()}</style>`;

    this._bindListEvents(rewards);
  }

  _bindListEvents(rewards) {
    this.querySelector(".sc-toggle-add")?.addEventListener("click", () => {
      this._showAddForm = true;
      this._editingId = null;
      this._renderForm(this._addFormHtml());
    });
    this.querySelectorAll(".sc-edit-btn").forEach(b => b.addEventListener("click", () => {
      const r = rewards.find(x => x.reward_id === b.dataset.id);
      if (!r) return;
      this._editingId = r.reward_id;
      this._showAddForm = false;
      this._renderForm(this._editFormHtml(r));
    }));
    this.querySelectorAll(".sc-del-btn").forEach(b => b.addEventListener("click", () => {
      if (confirm(`Delete "${b.dataset.name}"?`)) {
        this._hass.callService("sticker_chart", "remove_reward", { reward_id: b.dataset.id });
        this._refreshAfterAction(2000);
      }
    }));
    this.querySelectorAll(".sc-auto-link").forEach(l => l.addEventListener("click", () => {
      window.location.href = `/config/automation/edit/${l.dataset.auto.replace("automation.", "")}`;
    }));
  }

  _renderForm(html) {
    const container = this.querySelector(".sc-form-container");
    if (!container) return;
    container.innerHTML = html;
    this._bindFormEvents();
  }

  _bindFormEvents() {
    this.querySelectorAll(".sc-cancel").forEach(b => b.addEventListener("click", () => {
      this._resetFormState();
      this.querySelector(".sc-form-container").innerHTML = "";
    }));
    this.querySelector(".sc-save-edit")?.addEventListener("click", () => this._doEdit());
    this.querySelector(".sc-save-add")?.addEventListener("click", () => this._doAdd());
  }

  _editFormHtml(r) {
    return `
      <div class="sc-form" data-form="edit" data-id="${r.reward_id}">
        <div class="sc-form-title">Editing: ${r.name}</div>
        ${this._fieldsHtml(r)}
        <div class="sc-form-btns">
          <button class="sc-btn sc-btn-cancel sc-cancel">Cancel</button>
          <button class="sc-btn sc-btn-save sc-save-edit">Save</button>
        </div>
      </div>`;
  }

  _addFormHtml() {
    return `
      <div class="sc-form" data-form="add" style="border-color:#4caf50;">
        <div class="sc-form-title">New Reward</div>
        ${this._fieldsHtml({ name: "", cost: "", icon: "mdi:star", description: "", automation_id: "" })}
        <div class="sc-form-btns">
          <button class="sc-btn sc-btn-cancel sc-cancel">Cancel</button>
          <button class="sc-btn sc-btn-save sc-save-add" style="background:#4caf50;">Add</button>
        </div>
      </div>`;
  }

  _fieldsHtml(r) {
    return `
      <label>Name<input type="text" name="name" value="${r.name}" placeholder="Movie Night"></label>
      <label>Cost<input type="number" name="cost" value="${r.cost}" min="1" placeholder="10"></label>
      <label>Icon<input type="text" name="icon" value="${r.icon}" placeholder="mdi:star"></label>
      <label>Description<input type="text" name="description" value="${r.description}" placeholder="Optional"></label>
      <label>Automation<input type="text" name="automation_id" value="${r.automation_id}" placeholder="automation.xyz (optional)"></label>`;
  }

  _doEdit() {
    const f = this.querySelector('[data-form="edit"]');
    if (!f) return;
    const data = { reward_id: f.dataset.id };
    const v = n => f.querySelector(`[name="${n}"]`).value.trim();
    if (v("name")) data.reward_name = v("name");
    const c = parseInt(v("cost")); if (c > 0) data.cost = c;
    if (v("icon")) data.icon = v("icon");
    data.description = v("description");
    if (v("automation_id")) data.automation_id = v("automation_id");
    this._hass.callService("sticker_chart", "update_reward", data);
    this._refreshAfterAction();
  }

  _doAdd() {
    const f = this.querySelector('[data-form="add"]');
    if (!f) return;
    const v = n => f.querySelector(`[name="${n}"]`).value.trim();
    const name = v("name"), cost = parseInt(v("cost"));
    if (!name || !cost || cost < 1) { alert("Name and cost required."); return; }
    const data = { reward_name: name, cost, icon: v("icon") || "mdi:star", description: v("description") };
    if (v("automation_id")) data.automation_id = v("automation_id");
    this._hass.callService("sticker_chart", "add_reward", data);
    this._refreshAfterAction(2500); // add_reward triggers reload, needs more time
  }

  _styles() { return `
    .sc-wrap{padding:20px}
    .sc-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
    .sc-title{font-size:18px;font-weight:700}
    .sc-list{display:flex;flex-direction:column;gap:8px}
    .sc-row{display:flex;align-items:center;gap:12px;padding:14px 16px;
      background:var(--card-background-color,#1e1e1e);border:1px solid var(--divider-color,#333);border-radius:12px}
    .sc-icon-box{width:44px;height:44px;border-radius:12px;background:rgba(3,169,244,0.12);
      display:flex;align-items:center;justify-content:center;flex-shrink:0}
    .sc-info{flex:1;min-width:0}
    .sc-name{font-size:16px;font-weight:600}
    .sc-meta{font-size:13px;opacity:0.6;margin-top:2px}
    .sc-auto{font-size:12px;opacity:0.5;margin-top:4px;cursor:pointer;text-decoration:underline}
    .sc-auto:hover{opacity:0.8}
    .sc-auto-none{font-size:12px;opacity:0.25;margin-top:4px}
    .sc-actions{display:flex;gap:6px;flex-shrink:0}
    .sc-btn{border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer}
    .sc-btn-add{background:#4caf50;color:#fff}
    .sc-btn-edit{background:var(--primary-color,#03a9f4);color:#fff}
    .sc-btn-del{background:#f44336;color:#fff;padding:8px 10px}
    .sc-btn-save{background:var(--primary-color,#03a9f4);color:#fff}
    .sc-btn-cancel{background:var(--secondary-background-color,#555);color:#fff}
    .sc-form{padding:16px;margin-top:12px;border:2px solid var(--primary-color,#03a9f4);border-radius:12px;
      background:var(--card-background-color,#1e1e1e)}
    .sc-form-title{font-size:14px;font-weight:700;margin-bottom:8px}
    .sc-form label{display:block;font-size:12px;font-weight:600;opacity:0.6;margin-top:10px;
      text-transform:uppercase;letter-spacing:0.5px}
    .sc-form label:first-of-type{margin-top:0}
    .sc-form input{width:100%;padding:10px 12px;border-radius:8px;border:1px solid var(--divider-color,#444);
      background:var(--secondary-background-color,#2a2a2a);color:var(--primary-text-color,#fff);
      font-size:14px;box-sizing:border-box;margin-top:4px}
    .sc-form-btns{display:flex;gap:8px;margin-top:14px;justify-content:flex-end}
  `; }
}

customElements.define("sticker-admin-rewards-card", StickerAdminRewardsCard);


// ── Sticker Admin Kid Card ──────────────────────────────────────────────────
// Targeted DOM updates — only rebuilds the balance text and pending section,
// not the whole card. Event listeners survive across updates.

class StickerAdminKidCard extends HTMLElement {
  constructor() {
    super();
    this._lastKey = null;
    this._built = false;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config) return;
    const kid = this._getKid();
    if (!kid) return;
    const key = `${kid.balance}|${JSON.stringify(kid.pending)}`;
    if (key === this._lastKey) return;
    this._lastKey = key;

    if (!this._built) {
      this._buildShell(kid);
      this._built = true;
    } else {
      this._updateData(kid);
    }
  }

  setConfig(config) {
    if (!config.child_id) throw new Error("child_id is required");
    this._config = config;
  }

  getCardSize() { return 3; }
  static getStubConfig() { return { child_id: "", color: "#03a9f4" }; }

  _getKid() {
    const cid = this._config.child_id;
    for (const [eid, state] of Object.entries(this._hass.states)) {
      if (!eid.startsWith("sensor.") || !eid.includes("sticker_balance")) continue;
      if (state.attributes.child_id !== cid) continue;
      const pendingEid = eid.replace("sticker_balance", "pending_requests");
      const pendingState = this._hass.states[pendingEid];
      return {
        child_id: cid,
        name: state.attributes.child_name || "Kid",
        balance: parseInt(state.state) || 0,
        pending: pendingState?.attributes?.pending_requests || [],
      };
    }
    return null;
  }

  _buildShell(k) {
    const color = this._config.color || "#03a9f4";
    this.innerHTML = `
      <ha-card>
        <div class="sk-wrap">
          <div class="sk-header">
            <div class="sk-avatar" style="background:${color};">${k.name.charAt(0)}</div>
            <div class="sk-info">
              <div class="sk-name">${k.name}</div>
              <div class="sk-balance-text">${k.balance} ⭐ stickers</div>
            </div>
          </div>
          <div class="sk-buttons">
            <button class="sc-btn sk-grant" data-amount="1" style="background:#4caf50;color:#fff;">+1</button>
            <button class="sc-btn sk-grant" data-amount="5" style="background:#2196f3;color:#fff;">+5</button>
            <button class="sc-btn sk-grant" data-amount="10" style="background:#9c27b0;color:#fff;">+10</button>
            <button class="sc-btn sk-revoke" data-amount="1" style="background:#f44336;color:#fff;">−1</button>
            <button class="sc-btn sk-revoke" data-amount="5" style="background:#f44336;color:#fff;">−5</button>
          </div>
          <div class="sk-pending-container"></div>
        </div>
      </ha-card>
      <style>
        .sk-wrap{padding:20px}
        .sk-header{display:flex;align-items:center;gap:14px;margin-bottom:14px}
        .sk-avatar{width:52px;height:52px;border-radius:50%;color:#fff;
          font-size:24px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0}
        .sk-info{flex:1}
        .sk-name{font-size:20px;font-weight:700}
        .sk-balance-text{font-size:15px;opacity:0.6;margin-top:2px}
        .sk-buttons{display:flex;gap:8px;flex-wrap:wrap}
        .sk-buttons .sc-btn{padding:10px 18px;font-size:15px;font-weight:700;border-radius:10px;flex:1;min-width:50px}
        .sc-btn{border:none;border-radius:8px;cursor:pointer}
        .sk-pending-section{margin-top:14px;padding-top:14px;border-top:1px solid var(--divider-color,#333)}
        .sk-pending-label{font-size:12px;font-weight:600;opacity:0.5;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px}
        .sk-pending-row{display:flex;align-items:center;justify-content:space-between;gap:8px;
          padding:10px 12px;background:rgba(255,152,0,0.08);border-radius:8px;margin-bottom:6px}
        .sk-pending-info{display:flex;align-items:center;gap:8px}
        .sk-pending-name{font-size:14px;font-weight:600}
        .sk-pending-cost{font-size:13px;opacity:0.5}
        .sk-pending-actions{display:flex;gap:6px}
        .sk-approve{background:#4caf50!important;color:#fff!important;padding:8px 14px!important;font-size:13px!important;font-weight:600!important}
        .sk-deny{background:#f44336!important;color:#fff!important;padding:8px 14px!important;font-size:13px!important;font-weight:600!important}
      </style>`;

    // These listeners persist — they don't get rebuilt
    const cid = k.child_id;
    this.querySelectorAll(".sk-grant").forEach(b => b.addEventListener("click", () => {
      this._hass.callService("sticker_chart", "grant_stickers", {
        child_id: cid, amount: parseInt(b.dataset.amount), reason: "Sticker admin"
      });
    }));
    this.querySelectorAll(".sk-revoke").forEach(b => b.addEventListener("click", () => {
      this._hass.callService("sticker_chart", "revoke_stickers", {
        child_id: cid, amount: parseInt(b.dataset.amount), reason: "Sticker admin"
      });
    }));

    this._updateData(k);
  }

  _updateData(k) {
    // Update balance text without rebuilding
    const balEl = this.querySelector(".sk-balance-text");
    if (balEl) balEl.textContent = `${k.balance} ⭐ stickers`;

    // Update pending section — this part does get rebuilt but it's small
    const container = this.querySelector(".sk-pending-container");
    if (!container) return;

    if (k.pending.length === 0) {
      container.innerHTML = "";
      return;
    }

    let reqRows = "";
    for (const req of k.pending) {
      reqRows += `
        <div class="sk-pending-row">
          <div class="sk-pending-info">
            <span class="sk-pending-name">${req.reward_name}</span>
            <span class="sk-pending-cost">${req.reward_cost} ⭐</span>
          </div>
          <div class="sk-pending-actions">
            <button class="sc-btn sk-approve" data-id="${req.request_id}">✓ Approve</button>
            <button class="sc-btn sk-deny" data-id="${req.request_id}">✕ Deny</button>
          </div>
        </div>`;
    }

    container.innerHTML = `
      <div class="sk-pending-section">
        <div class="sk-pending-label">⏳ Pending Requests</div>
        ${reqRows}
      </div>`;

    // Rebind only the pending buttons
    container.querySelectorAll(".sk-approve").forEach(b => b.addEventListener("click", () => {
      this._hass.callService("sticker_chart", "approve_redemption", { request_id: b.dataset.id });
    }));
    container.querySelectorAll(".sk-deny").forEach(b => b.addEventListener("click", () => {
      this._hass.callService("sticker_chart", "deny_redemption", { request_id: b.dataset.id });
    }));
  }
}

customElements.define("sticker-admin-kid-card", StickerAdminKidCard);


// ── Card Registration ───────────────────────────────────────────────────────

window.customCards = window.customCards || [];
window.customCards.push(
  {
    type: "sticker-admin-rewards-card",
    name: "Sticker Admin Rewards Card",
    description: "Manage the sticker chart reward catalog",
    preview: true,
  },
  {
    type: "sticker-admin-kid-card",
    name: "Sticker Admin Kid Card",
    description: "Manage stickers and approve/deny for a single kid",
    preview: true,
  },
);

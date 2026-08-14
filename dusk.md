---
dusk: v1alpha1
namespace: stout
kind: repository
name: ha-sticker-chart
title: Sticker Chart
attributes:
  language: python
  visibility: public
  distribution: hacs
---

A Home Assistant custom integration, domain `sticker_chart`, for children's sticker reward charts: a balance per child, a reward catalogue shared across all of them, and a redemption request that a parent approves or denies.

Install it through HACS as a custom repository of type integration, or copy `custom_components/sticker_chart/` into a config directory and restart.
It has no dependencies beyond Home Assistant itself and needs Python 3.12.
Everything is configured after the fact, either through the options flow or through the services, so adding the integration asks nothing.

## The entity model

All state lives in one Home Assistant `Store` at `.storage/sticker_chart`, holding four collections: `children`, `rewards`, `pending_requests`, and an append-only `history`.
Children and rewards are separate registries with eight-character hex ids, and the entities are their cross product.
Each child gets a balance sensor and a pending-count sensor; each child and reward pair gets a redeem button, disabled when the balance is short or a request for that reward is already outstanding.
Unique ids are `sticker_chart_{child}_balance`, `sticker_chart_{child}_pending` and `sticker_chart_{child}_{reward}_redeem`, and the entities are grouped under a device per child.

Nothing parent-facing is built in.
The integration fires `sticker_chart_redemption_requested`, `_approved`, `_denied`, `_stickers_granted` and `_stickers_revoked` on the bus and exposes ten services; the notification, the approve and deny buttons on it, and the automation a reward triggers are all automations you write, with worked examples in the README.

## Gotchas

**Stickers are deducted when the request is made, not when it is approved.**
`async_request_redemption` debits the balance and records `cost_deducted` on the pending request, approval only clears the request, and denial refunds it and writes a `refund` history row.
The README's service table claims approval deducts and denial leaves the balance untouched, and it is wrong.

**Adding or removing a child or a reward reloads the config entry.**
Entities are only constructed in `async_setup_entry`, so there is no other way to make them appear, and removal has to delete the registry rows itself through `StickerChartStore._purge_entities` or the orphans persist in the entity registry forever.

**The two Lovelace cards under `custom_components/sticker_chart/www/` are not registered by anything.**
No static path is served and no frontend resource is added, so they have to be copied into the config `www/` directory and added as dashboard resources by hand.
The README predates them and describes building the dashboards out of plain sensor and button cards instead.

CI runs HACS validation, hassfest, and a pytest suite that covers the store directly (`tests/test_store.py`); the platforms and the service layer are not covered.

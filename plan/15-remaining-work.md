# Plan 15: Remaining Work

## Current status

Plan 14A-14F is functionally implemented for the demo-first order, payment, shipping, admin, and shipper flow.

Verified without Docker:

- `frontend`: `npm run build` pass.
- `frontend`: `npm run lint` pass.
- `order-service`: SQLite tests pass.
- `payment-service`: SQLite tests pass.
- `shipping-service`: SQLite tests pass.
- `staff-service`: SQLite tests pass.

## Remaining work

### 1. Full end-to-end verification

Run the full business flow against real services, gateway, and persistent databases:

```text
Customer add product
Customer checkout
Cart clears
Order appears as PENDING
Admin verifies order
Customer pays
Admin creates shipment
System/admin assigns shipper
Shipper starts delivery
Shipper marks delivered
Admin completes order
Customer sees completed timeline
```

The lightweight SQLite tests cover service logic, but they do not replace full gateway/service integration.

### 2. Demo readiness update

Update Plan 13 artifacts after Plan 14 changes:

- demo script;
- defense checklist;
- route/account checklist;
- evidence summary for checkout, payment, shipment, shipper, admin ops;
- screenshots or screen recording notes if needed.

### 3. Test account and seed data

Prepare deterministic demo data:

- at least one customer account;
- one admin account;
- one shipper account;
- shipper profile with lat/lng;
- products with stock;
- known delivery coordinates for auto-assignment.

### 4. Gateway smoke test

When memory allows, run a small subset through the API gateway instead of direct service tests:

- `GET /api/orders`;
- `POST /api/orders`;
- `GET /api/payments`;
- `GET /api/shipping/shipments`;
- `POST /api/shipping/shipments/:id/assign_shipper`;
- `POST /api/shipping/shipments/:id/ship`;
- `POST /api/shipping/shipments/:id/deliver`.

### 5. Admin UX polish

Optional improvements before final demo:

- route admin dashboard queue links directly to the selected order detail;
- show clearer warning when no shipper profile exists;
- show payment transaction history in admin detail;
- show shipment assignment history separately from tracking events.

### 6. Shipper UX polish

Optional improvements:

- add explicit accept order action if required by rubric;
- show map/deep link for delivery address;
- show assigned time and latest location more prominently;
- add route-level detail page component if the current combined page becomes too dense.

### 7. Post-Plan 14 sequence

After this business flow is stable, continue with:

```text
13-defense-demo-readiness
12-evaluation-ablation
12a-recommendation-evaluation-ablation
12b-chat-grounding-evaluation
11-deep-model-mvp
```

Plan 13 should be updated first because Plan 14 changed the main demo journey.

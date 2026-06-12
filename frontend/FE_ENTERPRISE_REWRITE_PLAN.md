# Enterprise Premium Commerce FE Rewrite Plan

## Summary

Rewrite the frontend into a Premium Commerce customer experience plus Enterprise Admin console using Ant Design as the primary UI kit. Preserve the working API client/session store where practical, but replace the demo-style layout, pages, and CSS.

## Key Changes

- Replace the single app shell with Customer, Admin, and Auth layouts.
- Use Ant Design `ConfigProvider` theme plus a focused global stylesheet.
- Add reusable shared UI wrappers: page headers, status tags, money/date formatting, data states, product cards, metric cards.
- Extend frontend API coverage for staff auth, admin product operations, order status changes, interactions, graph, and model status.
- Add customer routes for storefront, cart, checkout, orders, profile, and assistant.
- Add admin routes for dashboard, products, orders, payments, shipments, interactions, graph, and model status.

## Implementation Steps

1. Foundation: install Ant Design packages, configure theme, create layouts and route tree.
2. Customer storefront: premium home, product browsing, product detail, rich cart, checkout, order detail, assistant.
3. Admin console: staff login, dashboard, CRUD-oriented product pages, order/payment/shipment management, interactions, graph, model status.
4. Polish: loading/empty/error states, responsive checks, consistent formatting, and build/lint verification.

## Test Plan

- Run `npm run build`.
- Run `npm run lint`.
- Manually verify customer auth, products, cart, checkout, orders, assistant, admin login, admin CRUD/lifecycle pages, analytics, graph, and model status.

## Assumptions

- Backend APIs remain unchanged.
- Gateway remains `http://localhost`.
- Ant Design and `@ant-design/icons` are allowed dependencies.
- Admin-only actions use the configured internal admin key in frontend dev settings when needed.

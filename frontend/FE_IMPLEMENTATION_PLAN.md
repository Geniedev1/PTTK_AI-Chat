# Frontend Implementation Plan (Full System)

## 1. Objective

Build one unified frontend for the entire backend system, not only AI/chat.

Primary goals:
1. Integrate all gateway services documented in BACKEND_API_DOCS.
2. Deliver a modern, responsive UI for customer and admin/staff workflows.
3. Keep bug rate low via strict typing, runtime validation, and test gates.
4. Run frontend Docker together with backend Docker stack.

## 2. Source of Truth

Main API contract documents:
1. BACKEND_API_DOCS.md (full system map)
2. ai-service/docs/frontend-api.md (AI request/response details)

Gateway base URL for frontend:
- http://localhost

Service prefixes:
1. /api/staff/
2. /api/customers/
3. /api/cart/
4. /api/products/
5. /api/orders/
6. /api/interactions/
7. /api/ai/

## 3. Frontend Scope

## 3.1 Customer App

1. Authentication
- Customer register
- Customer login
- Customer profile view and update

2. Product discovery
- Category listing
- Product listing with filter/sort/search
- Product detail
- In-stock view

3. Cart and checkout
- Current cart
- Add/remove/update quantity
- Clear cart
- Create order from cart

4. Order tracking
- Order list by scope
- Order detail by scope

5. AI layer in customer app
- Recommendation modules on home/product/cart
- AI chat and retrieval source panel
- Profile snapshot and model status page (optional in user-facing app, required in QA/admin mode)

## 3.2 Staff/Admin App

1. Staff login and profile
2. Product management (create/update/delete/variant)
3. Order status management
4. Interaction analytics dashboards
- Data quality
- Top queries
- Product gaps
- Abandoned carts
- Category interest
- Signal weights
5. Graph operations
- Graph status
- Graph rebuild (internal admin key only)

## 3.3 Global Chat Widget (Messenger-style)

1. One fixed launcher icon on all pages.
2. Click icon to open floating chat window.
3. Minimize and restore behavior like Facebook Messenger.
4. Position fixed at bottom-right across route changes.
5. Conversation state persists while navigating pages.

## 4. Recommended Tech Stack

1. Vite + React + TypeScript
2. React Router
3. TanStack Query
4. Axios
5. Zod (runtime schema validation)
6. Zustand (global app/chat/session stores)
7. UI system: choose one and keep consistent
- MUI
- Or shadcn/ui + Tailwind
8. Testing
- Vitest + React Testing Library
- Playwright smoke E2E

## 5. Core Frontend Architecture

Proposed structure:

```text
frontend/
  src/
    app/
      router/
      providers/
      layout/
    modules/
      auth/
      catalog/
      cart/
      orders/
      ai/
      interactions/
      staff/
      chat-widget/
    pages/
      customer/
      admin/
    shared/
      api/
      schemas/
      types/
      components/
      hooks/
      utils/
      constants/
      styles/
  tests/
  Dockerfile.dev
  Dockerfile
  nginx.conf
```

Architecture rules:
1. UI components never call HTTP directly.
2. API calls only in module service layer.
3. Every response is validated by Zod before use.
4. Route-level error boundary for crash safety.

## 6. API Integration Matrix by Module

## 6.1 Auth Module

Customer:
1. POST /api/customers/register/
2. POST /api/customers/login/
3. GET /api/customers/profile/
4. PUT /api/customers/update_profile/

Staff:
1. POST /api/staff/login/
2. GET /api/staff/me/
3. POST /api/staff/register/ (admin tool)

Headers:
- Authorization: Token <token>

## 6.2 Catalog Module

1. GET /api/products/categories/
2. GET /api/products/categories/{id}/
3. GET /api/products/
4. GET /api/products/{id}/
5. GET /api/products/search/
6. GET /api/products/in_stock/

Admin actions:
1. POST /api/products/
2. PUT /api/products/{id}/
3. DELETE /api/products/{id}/
4. POST /api/products/{id}/variants/

Headers for admin actions:
- X-Internal-Admin-Key (only in privileged admin screen)

## 6.3 Cart Module

1. GET /api/cart/current
2. POST /api/cart/add_product
3. POST /api/cart/remove_product
4. POST /api/cart/update_quantity
5. POST /api/cart/clear_cart

Headers:
- X-Cart-Session-Key persisted and reused

## 6.4 Order Module

1. GET /api/orders
2. GET /api/orders/{id}
3. POST /api/orders
4. POST /api/orders/{id}/update_status (admin)

Scope rules for GET:
- customer_id query or X-Cart-Session-Key header required

Admin header:
- X-Internal-Admin-Key for update_status

## 6.5 Interaction Module

Events:
1. GET /api/interactions/events
2. POST /api/interactions/events
3. GET /api/interactions/events/data_quality
4. GET /api/interactions/events/top_queries
5. GET /api/interactions/events/product_gaps
6. GET /api/interactions/events/abandoned_carts
7. GET /api/interactions/events/category_interest
8. GET /api/interactions/events/signal_weights

Graph:
1. GET /api/interactions/graph/status
2. POST /api/interactions/graph/rebuild
3. GET /api/interactions/graph/user_interest
4. GET /api/interactions/graph/product_neighbors
5. GET /api/interactions/graph/query_paths
6. GET /api/interactions/graph/similar_users

## 6.6 AI Module

1. GET /api/ai/recommend/home
2. GET /api/ai/recommend/product-detail
3. GET /api/ai/recommend/cart
4. GET /api/ai/recommend/profile/snapshot
5. GET /api/ai/profile/snapshot
6. GET /api/ai/models/status
7. POST /api/ai/chat
8. POST /api/ai/chat/retrieve

## 7. Route Plan (Page by Page)

## 7.1 Customer Routes

1. /auth/register
- Customer registration

2. /auth/login
- Customer login

3. /profile
- Profile display and update

4. /products
- Product list with filters/sort/search

5. /products/:id
- Product detail
- Related recommendations widget

6. /cart
- Cart actions and cart recommendations

7. /checkout
- Create order from current cart

8. /orders
- Order history in current scope

9. /orders/:id
- Order detail

10. /assistant
- Full AI chat page (advanced mode)

## 7.2 Admin Routes

1. /admin/login
2. /admin/products
3. /admin/orders
4. /admin/interactions
5. /admin/graph
6. /admin/model-status

## 7.3 Global Overlay

1. GlobalChatWidget mounted once in AppShell.
2. Visible on all customer routes.
3. Optional disable on specific admin routes if needed.

## 8. Low-Bug Engineering Rules

1. TypeScript strict mode is mandatory.
2. Add Zod schema for each endpoint response.
3. Standardize API error shape:
- detail-based error
- serializer field errors
4. Every page must implement 4 UI states:
- loading
- success
- empty
- error
5. Persist and rotate headers correctly:
- Authorization token
- X-Cart-Session-Key
- X-Request-ID
6. Respect trailing slash differences across services.
7. Defensive rendering for nullable fields.
8. Centralized retry and timeout policy.

## 9. Floating Chat Widget Spec

Behavior:
1. Circular launcher at bottom-right.
2. Opens floating chat panel.
3. Supports minimize, close, reopen.
4. Keeps messages when route changes.

Size and placement:
1. Launcher: 56px desktop, 52px mobile.
2. Desktop panel: 360-400px width, 560-680px height.
3. Mobile panel: full-screen style.
4. High z-index above page content.

Accessibility:
1. Enter to open from launcher.
2. Esc to close panel.
3. Focus trap while panel is open.
4. aria-label for launcher and controls.

## 10. Delivery Phases

## Phase A: Foundation (1 day)

1. Bootstrap app and router.
2. Setup providers: query, store, theme.
3. Setup API client and header middleware.
4. Mount global chat launcher shell.

## Phase B: Core Commerce (2 days)

1. Auth flows (customer).
2. Catalog pages and product detail.
3. Cart actions and checkout order create.
4. Order list/detail pages.

## Phase C: AI and Chat (2 days)

1. Recommendation widgets in home/detail/cart.
2. Full AI chat page.
3. Messenger-style global chat widget.
4. Profile snapshot and model status views.

## Phase D: Admin and Analytics (2 days)

1. Staff auth.
2. Product management CRUD screens.
3. Order status update screen.
4. Interaction analytics and graph tools.

## Phase E: QA and Hardening (1 to 1.5 days)

1. Unit tests for adapters and mappers.
2. Integration tests for key pages.
3. Smoke E2E:
- login
- browse and add cart
- create order
- open chat and send message
4. Performance and accessibility pass.

## 11. Docker Run Plan with Backend

## 11.1 Files

Create and maintain:
1. frontend/Dockerfile.dev
2. frontend/Dockerfile
3. frontend/nginx.conf

## 11.2 Compose Service

Add frontend service to root docker-compose:
1. Build: ./frontend
2. Port: 5173:5173 (dev)
3. Env:
- VITE_API_BASE_URL=http://localhost
4. Depends on api-gateway
5. Same network as backend services

## 11.3 Dev Command

1. docker compose up --build
2. Open frontend at http://localhost:5173
3. Frontend calls backend through gateway at http://localhost

## 12. Definition of Done

Frontend is done when:
1. All core customer flows work end to end.
2. All required admin tools work with proper access headers.
3. API integration covers all service groups in BACKEND_API_DOCS.
4. Global chat icon and popup window work on all target routes.
5. Lint, typecheck, tests, and build are green.
6. Frontend and backend run together in Docker reliably.

## 13. Risks and Mitigation

1. Risk: mismatch between docs and runtime response.
- Mitigation: Zod validation and adapter mapping layer.

2. Risk: wrong header/session handling.
- Mitigation: single API client with header interceptors and integration tests.

3. Risk: trailing slash mistakes by route.
- Mitigation: endpoint constants per service with explicit path style.

4. Risk: unstable cross-module state.
- Mitigation: module stores with clear boundaries and route-level tests.

5. Risk: over-coupled UI and backend payload.
- Mitigation: map DTO to UI view-models before render.

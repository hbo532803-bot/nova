# Nova Full-Stack Audit Report

Date: 2026-04-14 (UTC)

## Scope and method

- Reviewed repository structure for frontend (`frontend/`) and backend (`backend/`).
- Ran backend with Uvicorn and exercised core public + authenticated APIs.
- Ran frontend build and dev server, validated app shell serving.
- Performed static code review for UI/UX, integration, and responsiveness risks.

## Backend findings

### B1. Backend cannot boot with default environment (critical setup blocker)

- `backend/auth.py` throws runtime errors when `NOVA_SECRET_KEY` and admin credentials are not provided.
- This is correct from a security perspective, but currently behaves as a hard startup blocker with no fallback/developer mode.
- In this session, backend startup failed until all three env vars were injected.

Impact:
- Fresh local runs fail immediately.
- Frontend appears "broken" if backend never starts.

Suggestion:
- Add `.env.example` and explicit startup checks/documentation in root README.
- Consider clearer startup logging with exact missing variable names and next steps.

### B2. Order execution failure state is masked as completed

- `_run_order_execution` writes `status="COMPLETED"` even on exceptions, storing `{"error":"order_execution_failed"}`.
- API clients may treat failed jobs as successfully completed.

Impact:
- Misleading UX and incorrect business state.
- Frontend may show completion even when execution failed.

Suggestion:
- Introduce explicit terminal states: `FAILED` vs `COMPLETED`.
- Include normalized error metadata (`error_code`, `retryable`, `message`).

### B3. Oversized payload returned from order status endpoint

- `GET /api/order/status/{id}` returns full nested execution payload when completed.
- Payload can become very large and includes deeply nested artifacts.

Impact:
- Unnecessary network + render overhead for polling clients.
- Increases latency and frontend memory churn.

Suggestion:
- Return concise status DTO from `/order/status` and provide heavy details via dedicated `/order/result`.
- Add pagination/summary for artifacts.

## Frontend findings (high-priority deep review)

### F1. Price rendering bug introduces double dollar sign

- Product UI prepends `$` in JSX while backend already returns `estimated_price` strings with `$` (e.g., `$1,500`).
- UI can render `$$1,500`.

Impact:
- Pricing display looks broken/unprofessional.

Suggestion:
- Render as-is when value is already a formatted currency string.
- Normalize price type contract (number vs formatted string) across API/UI.

### F2. Value projection math breaks for formatted currency strings (critical UX logic bug)

- `planPrice` is computed with `Number(selectedOffer?.estimated_price || 1200)`.
- With values like `$1,500`, `Number("$1,500")` becomes `NaN`, cascading into `estimatedLeads` and `potentialRevenue`.

Impact:
- "Value Projection" panel can show invalid figures (`NaN`) or inconsistent values.

Suggestion:
- Parse currency safely (strip symbols/commas) or pass numeric `estimated_price_value` from backend.

### F3. Execution result mapping mismatch for preview URL

- Product page expects `result?.website_url || result?.preview_url || result?.deployment_url`.
- Backend order status shape nests execution output and may not expose these root fields.

Impact:
- Preview iframe/link may never appear even when usable data exists deeper in payload.

Suggestion:
- Introduce stable API response contract (`result.preview_url`, `result.summary`, etc.).
- Add adapter function in frontend to map backend payloads safely.

### F4. Responsiveness gaps in admin shell

- `MainLayout` uses fixed full-height flex + fixed-width sidebar (`220px`) with no mobile collapse behavior.
- No media-query strategy for sidebar/topbar interaction in admin routes.

Impact:
- Likely cramped or unusable admin navigation on mobile/tablet.

Suggestion:
- Add responsive breakpoint behavior (drawer/hamburger on small screens).
- Shift inline layout styles into centralized responsive CSS.

### F5. Polling-heavy data flow can be expensive on weak networks/devices

- `useNovaSystem` polls every 5s and every 30s triggers many parallel heavy endpoints.
- Large datasets plus repeated store writes can hurt performance.

Impact:
- Potential jank in admin pages, excess backend/API load.

Suggestion:
- Add adaptive polling, incremental diff fetches, and focus/visibility throttling.
- Memoize derived selectors and limit deep payload writes.

## Critical bugs (high priority)

1. Product value math with formatted currency => `NaN` projections (frontend).
2. Price UI double currency symbol rendering (frontend).
3. Order failure state written as `COMPLETED` (backend semantics).
4. Startup hard-fail when env vars absent without clear local setup defaults (operational blocker).

## Commands executed (evidence)

- Backend start attempts and successful run using:
  - `python -m uvicorn backend.frontend_api.app:app --host 127.0.0.1 --port 8000`
  - `NOVA_SECRET_KEY=devsecret NOVA_ADMIN_USER=admin NOVA_ADMIN_PASS=admin123 python -m uvicorn backend.frontend_api.app:app --host 127.0.0.1 --port 8000`
- Backend API checks with `curl`:
  - `/api/status`, `/api/system/health`, `/api/login`, `/api/agents`, `/api/order/create`, `/api/order/confirm`, `/api/order/status/{id}`
  - admin-console endpoints used by frontend (`/api/system/state`, `/api/confidence`, `/api/commands`, `/api/social/console`, etc.)
- Frontend checks:
  - `cd frontend && npm run build`
  - `cd frontend && VITE_API_URL=http://127.0.0.1:8000 npm run dev`
  - `curl http://127.0.0.1:3000/` and `/product`

## Notes

- No source code behavior was changed during this audit run.
- This report captures observed runtime behavior plus static review findings to prioritize fixes.

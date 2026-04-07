# Nova Frontend (Product + Admin)

This frontend contains two separate experiences:

- **User Product UI**: `/` and `/product`
- **Admin UI**: `/login` then protected routes like `/dashboard`

## 1) Install dependencies

```bash
npm install
```

## 2) Configure backend API URL

Create a `.env` file in `frontend/`:

```bash
VITE_API_URL=http://127.0.0.1:8000
```

Compatibility fallback is also supported for:

```bash
REACT_APP_API_URL=http://127.0.0.1:8000
```

## 3) Run development server

Use either command:

```bash
npm run dev
```

or

```bash
npm start
```

The app runs at:

- `http://localhost:3000`

## 4) Build production bundle

```bash
npm run build
```

## Backend + CORS checklist

- Backend must be running (default expected: `http://127.0.0.1:8000`).
- If requests fail in browser with CORS errors, ensure backend CORS allows origin:
  - `http://localhost:3000`
- Ensure frontend `.env` API URL matches backend host/port exactly.

## Product flow tested in UI

1. User enters goal in `/product`.
2. Frontend calls `POST /api/order/create`.
3. User selects a plan and completes fake payment gate.
4. Frontend calls `POST /api/order/confirm`.
5. Frontend polls `GET /api/order/status/{order_id}` and renders result/value cards.

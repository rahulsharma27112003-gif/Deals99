# Deals99 Enterprise Audit Report

**Date:** 2026-05-21  
**Scope:** `Deals99/backend` + `Deals99/Frontend` + deployment configs

---

## 1. Architecture Summary

| Layer | Technology | Entry |
|-------|------------|--------|
| API | Django 4.2 + DRF + SimpleJWT | `/api/`, `/api/v1/` |
| Admin API | `admin_dashboard` app | `/api/admin/`, `/api/v1/admin/` |
| Auth | `core.User` (email login) + JWT + HttpOnly refresh cookie | `/api/auth/*` |
| DB | SQLite (dev) / PostgreSQL (prod via env) | `config/settings/base.py` |
| Cache/Celery | Redis (prod); LocMem (dev/tests) | `USE_REDIS_CACHE=True` |
| Frontend | Static HTML + ES modules (`api.js`, `script.js`) | Served at `/` in DEBUG |

**Apps:** `core` (User), `api` (catalog, cart, orders, payments), `admin_dashboard` (KPIs).

---

## 2. Problems Found (Root Causes)

| Issue | Risk | Root cause |
|-------|------|------------|
| Broken `CartManager.addItem` in `script.js` | **Critical** | Syntax corruption — module failed to load |
| Frontend `/api/users/` vs backend | **High** | Admin users live at `/api/admin/users/` only |
| DRF pagination not handled in frontend | **High** | `fetchProducts()` returned `{results:[]}` treated as array |
| Dual auth (JWT + mock localStorage login) | **High** | `login.html` faked login; API never called |
| Checkout used localStorage only | **High** | `create_from_cart` never invoked |
| Redis required in tests | **Medium** | Default cache backend pointed at localhost:6379 |
| RBAC role mismatch (`SUPERADMIN` vs `super_admin`) | **Medium** | Custom User roles not normalized in permissions |
| Refresh cookie path `/api/auth/refresh/` only | **Medium** | Cookie not sent for all API paths |
| Notifications unwired | **Medium** | `NotificationTrigger` not called from order service |
| `Order.payment_method` without choices | **Low** | `get_payment_method_display()` failed in emails |
| Public product write (`AllowAny` on POST) | **High** | `ProductViewSet` allowed anonymous creates |
| E2E test syntax error + slow default run | **Low** | Invalid assert line; Playwright in `manage.py test` |

---

## 3. Fixes Applied

### Backend
- **Services layer:** `api/services/orders.py`, `api/services/dashboard.py`
- **RBAC:** `api/permissions.py` with role normalization + `core.backends.EmailBackend`
- **Admin routes:** `path('api/admin/', include('admin_dashboard.urls'))`
- **Security:** Product/category writes require `IsStaffOrAbove`; refresh cookie path `/`
- **Orders:** Stock validation, `StockTransaction`, notification triggers on create/status change
- **Order model:** `PAYMENT_METHOD_CHOICES`; migrations `0003`–`0006`
- **Health:** `GET /api/health/`
- **Settings:** `config/settings/base.py` (canonical), LocMem cache in dev/tests, `USE_REDIS_CACHE` flag
- **Register:** DEBUG returns JWT immediately; production uses email verification
- **Tests:** Admin tests use `core.User` email API; E2E skipped unless `RUN_E2E=1`

### Frontend
- **`api.js`:** Dynamic `getApiBase()`, `unwrapPaginated()`, admin endpoints, `updateOrder` alias
- **`script.js`:** Fixed `CartManager` (add/update/remove/sync), real login/register via API
- **`checkout.html`:** Calls `createOrder()` when authenticated
- **Pagination:** Featured/deals/products unwrap paginated responses

---

## 4. Frontend ↔ Backend Sync Matrix

| Frontend call | Backend endpoint | Status |
|---------------|------------------|--------|
| `loginUser` | `POST /api/auth/login/` | Fixed (email + password) |
| `registerUser` | `POST /api/auth/register/` | Fixed (field mapping) |
| `fetchProducts` | `GET /api/products/` | Fixed (pagination) |
| `addToCart` | `POST /api/cart/` `{product_id}` | Fixed |
| `createOrder` | `POST /api/orders/create_from_cart/` | Fixed (checkout) |
| `fetchUsers` | `GET /api/admin/users/` | Fixed |
| `fetchDashboardStats` | `GET /api/admin/dashboard/` | Fixed |
| `updateOrderStatus` | `PATCH /api/orders/{id}/update_status/` | OK |

---

## 5. Security

| Item | Status |
|------|--------|
| `SECRET_KEY` from env | OK |
| `DEBUG=False` default in base | OK |
| JWT + refresh rotation + blacklist | OK |
| CORS credentials + explicit origins | OK (dev allows all) |
| Staff-only product writes | Fixed |
| Admin APIs behind `IsAdminOrManager` | OK |
| Webhook signature verification | Present (Stripe/Razorpay) |
| Account lockout on failed login | OK (`core.User`) |

**Manual setup:** Production email SMTP, Stripe/Razorpay secrets, `ALLOWED_HOSTS`, HTTPS behind reverse proxy.

---

## 6. Deployment Readiness

```bash
# Local
cd Deals99/backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Docker
docker compose up --build
```

**Env vars:** See `Deals99/backend/.env.example` — `SECRET_KEY`, `DB_*`, `EMAIL_*`, `STRIPE_*`, `USE_REDIS_CACHE`.

**Test credentials (local):**
- Super admin: `superadmin@example.com` / `SuperAdmin123!`
- Manager: `manager@example.com` / `Manager123!`
- Customer: `customer@example.com` / `Customer123!`

---

## 7. Test Status

- **78 core tests** pass with `manage.py test` (E2E skipped by default).
- Run E2E: `RUN_E2E=1 pytest api/tests/test_e2e_frontend.py`

---

## 8. Remaining Recommendations

1. Wire **payment intent API** (create `Payment` on checkout for Stripe/Razorpay).
2. Replace **localStorage-only** flows on `products.html`, `cart.html` with API-driven UI.
3. Add **PATCH admin user** endpoint or document read-only user list.
4. Commit **Playwright baselines** or disable visual regression in CI.
5. Run `collectstatic` and configure **CDN** for frontend in production.

---

## 9. Final Status

| Area | Production-ready? |
|------|-------------------|
| Core API (catalog, cart, orders, auth) | Yes (with env config) |
| Admin dashboard API | Yes |
| Frontend API integration | Partial — index/checkout/login fixed; some pages still demo/localStorage |
| Docker/Postgres | Structured, needs env |
| E2E/Playwright | Optional (`RUN_E2E=1`) |

**What was broken:** Module parse error, auth/checkout desync, admin URL mismatch, Redis test failures, open product writes.  
**What was fixed:** End-to-end alignment for primary shopper and admin flows, security defaults, health check, test stability.

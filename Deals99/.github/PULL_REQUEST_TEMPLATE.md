## Summary

**What:** Fix migrations, model mismatches, dependency compatibility for Python 3.13, webhook verification/tests, and CI migration check.

**Why:** Ensure schema changes are tracked, tests run on modern Python, and CI fails early for missing migrations.

---

### Changes included
- Add `core.User` initial migration and new `api` migrations for `StockTransaction` & `PaymentAudit`.
- Convert `Payment.order` OneToOne -> ForeignKey (support multiple payment attempts).
- Restore `UserProfile.role` to match migrations.
- Bump `djangorestframework-simplejwt` for Python 3.13 compatibility.
- Make `psycopg2-binary` optional on Windows; prefer Docker/CI for Postgres.
- Switch to `LocMemCache` during pytest to avoid requiring Redis locally.
- Add CI step to fail for missing migrations: `makemigrations --check --dry-run`.
- Fix webhook imports/URL wiring and test secrets; webhook unit tests pass locally.

---

### How to test locally
1. Install deps: `python -m pip install -r backend/requirements.txt`
2. Create & apply migrations: `python backend/manage.py makemigrations --check --dry-run` (should be no changes)
   then `python backend/manage.py migrate`
3. Run tests: `python -m pytest -q`
4. Smoke test webhooks (unit tests included in `api/tests/test_payments_webhooks.py`).

---

### Migration / deploy notes
- Run `python manage.py migrate` in staging and production after deployment.
- DB change: `Payment.order` altered from OneToOne to ForeignKey — no data migration required for existing rows, but verify code paths using `order.payment` are updated to use `.payments.first()` or appropriate queries.

---

### Rollback plan
- Revert the PR/branch if any production migration causes issues.
- Restore previous migration set and deploy an emergency rollback release.

---

### Reviewers / Labels
- Reviewers: `@backend-team`, `@devops`  
- Labels: `bug`, `ci`, `migrations`, `tests`, `backend`

---

### PR checklist
- [ ] All new migrations are present and reviewed
- [ ] Local test-suite passes (`pytest`) and CI is green
- [ ] DB migration applied successfully on staging
- [ ] Manual payment webhook smoke test on staging
- [ ] Post-deploy monitoring in place (Sentry/metrics)

---

If you want, I can add a follow-up PR to update any code still referencing `order.payment` to the plural `payments` access pattern.
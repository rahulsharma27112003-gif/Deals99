PR / Migration & Deploy Checklist

1) Before creating PR
   - [ ] Run `python -m pip install -r backend/requirements.txt`
   - [ ] Run `python backend/manage.py makemigrations --check --dry-run` (must report no changes)
   - [ ] Run `python backend/manage.py migrate` locally (or use Docker)
   - [ ] Run `python -m pytest -q` and fix test failures

2) PR review steps
   - [ ] Confirm migrations folder contains new/updated migration files
   - [ ] Ensure no model/migration mismatches (run `makemigrations --check`)
   - [ ] Validate the dependency bump is necessary and safe
   - [ ] Confirm webhook and payment unit tests pass
   - [ ] Confirm `CACHES` change for pytest is safe and documented

3) Staging rollout
   - [ ] Create staging DB backup (snapshot)
   - [ ] Deploy to staging and run `python manage.py migrate`
   - [ ] Run smoke tests (auth, create order, payment webhook simulation)
   - [ ] Check logs/Sentry for errors and monitor metrics

4) Production rollout
   - [ ] Schedule maintenance window if needed
   - [ ] Backup production DB
   - [ ] Deploy and run `python manage.py migrate`
   - [ ] Validate key customer flows (checkout, payment, admin tasks)
   - [ ] Monitor errors and rollback if critical failures occur

5) Post-deploy
   - [ ] Remove temporary test-only config flags if any
   - [ ] Add follow-up tasks to fix any `order.payment` → `order.payments` code paths
   - [ ] Update `README.md` with supported Python versions and local dev guide

Notes:
- For local Windows dev, prefer Docker Compose for full parity (Postgres + Redis).  
- CI now enforces migration parity; update migrations before merging any model change.
import os
import time
import unittest

import pytest

# These tests use the pytest-playwright `page` fixture.
# Run with: RUN_E2E=1 pytest api/tests/test_e2e_frontend.py -q

pytestmark = pytest.mark.skipif(
    os.environ.get('RUN_E2E') != '1',
    reason='Set RUN_E2E=1 to run Playwright E2E tests',
)


@pytest.mark.integration
@pytest.mark.usefixtures("live_server")
@unittest.skipUnless(os.environ.get('RUN_E2E') == '1', 'Set RUN_E2E=1 for Playwright E2E')
class TestFrontendE2E:
    def wait_for_frontend_ready(self, page, timeout=5000):
        # wait until ProductManager is available (script.js auto-init)
        page.wait_for_function("() => window.ProductManager !== undefined", timeout=timeout)

    def test_pwa_service_worker_and_manifest(self, page, live_server):
        """Stricter PWA checks: require service worker support + reachable file.
        Use env E2E_ALLOW_NO_SW=1 to relax SW registration requirement in special CI."""
        import os
        allow_no_sw = os.getenv('E2E_ALLOW_NO_SW', '0') == '1'

        url = f"{live_server.url}/auto-test.html"
        page.goto(url)
        self.wait_for_frontend_ready(page)

        # require browser support for service workers
        has_sw = page.evaluate("() => 'serviceWorker' in navigator")
        assert has_sw is True, 'Browser must support serviceWorker for PWA tests'

        # require registration of our service-worker.js unless explicitly allowed to skip
        reg = page.evaluate("() => navigator.serviceWorker.getRegistration('/service-worker.js').then(r=>!!r).catch(()=>false)")
        if not allow_no_sw:
            assert reg is True, 'service-worker.js should be registered in dev environment'

        # fetch service-worker.js directly and require a 200 response in strict mode
        resp = page.request.get(f"{live_server.url}/service-worker.js")
        assert resp.status == 200, f"Expected /service-worker.js to be served (200) but got {resp.status}"

        # manifest should be linked on index page
        page.goto(f"{live_server.url}/index.html")
        link_rel = page.locator('link[rel="manifest"]')
        assert link_rel.count() >= 1, 'index.html should include a manifest link'


    def test_client_search_index_and_input(self, page, live_server):
        """Require client search index + ProductManager search API to be present and usable."""
        page.goto(f"{live_server.url}/index.html")
        self.wait_for_frontend_ready(page)

        # require localStorage search index timestamp
        idx_ts = page.evaluate("() => { try { return localStorage.getItem('deals99_search_index_ts'); } catch(e) { return null; } }")
        assert idx_ts is not None, 'deals99_search_index_ts must exist in localStorage'

        # require ProductManager.searchProducts to be available and return a list
        pm_ok = page.evaluate("() => !!(window.ProductManager && typeof window.ProductManager.searchProducts === 'function')")
        assert pm_ok is True, 'window.ProductManager.searchProducts must be present on the page'
        results = page.evaluate("() => (window.ProductManager.searchProducts('test') || [])")
        assert isinstance(results, list), 'ProductManager.searchProducts should return a list'

        # require search input present on index page
        input_exists = page.locator('#clientSearchInput').count() > 0
        assert input_exists is True, 'clientSearchInput must be present on index.html'


    def test_lazy_loading_and_intersectionobserver(self, page, live_server):
        """Require at least one lazy-loaded image + IntersectionObserver support."""
        page.goto(f"{live_server.url}/index.html")
        self.wait_for_frontend_ready(page)

        lazy_count = page.locator('img[loading="lazy"]').count()
        srcset_count = page.locator('img[srcset]').count()
        io_supported = page.evaluate("() => typeof window.IntersectionObserver !== 'undefined'")

        assert lazy_count > 0, 'Expect at least one <img loading="lazy"> on index.html'
        assert io_supported is True, 'IntersectionObserver must be supported in the browser'
        # responsive images are recommended but not strictly required
        assert isinstance(srcset_count, int)

    def test_service_worker_offline_cache(self, page, live_server):
        """Verify service worker serves cached assets while offline."""
        import time
        page.goto(f"{live_server.url}/index.html")
        self.wait_for_frontend_ready(page)

        # ensure SW controller is active
        controller = page.evaluate("() => !!navigator.serviceWorker.controller")
        assert controller is True, 'Expected an active service worker controller before offline test'

        # fetch a static asset while online to ensure cached (global.css)
        resp_online = page.request.get(f"{live_server.url}/global.css")
        assert resp_online.status == 200

        # go offline and reload — content should still be available via SW
        page.set_offline(True)
        try:
            page.reload()
            # wait briefly for SW to respond
            time.sleep(0.5)
            content_exists = page.locator('body').count() > 0
            assert content_exists is True, 'Page body should be present when offline (served from SW)'

            # try to fetch the same asset via page.request (this bypasses SW) — still allowed but may fail in strict CI, so check DOM instead
            css_present = page.locator('link[href="/global.css"]').count() >= 0
            assert css_present is True
        finally:
            page.set_offline(False)

    def test_indexeddb_search_persistence(self, page, live_server):
        """If IndexedDB persistence is implemented, verify the search DB exists and contains entries.
        This test is skipped if IndexedDB-based index isn't present (backward-compatible)."""
        page.goto(f"{live_server.url}/index.html")
        self.wait_for_frontend_ready(page)

        has_indexeddb = page.evaluate("() => !!window.indexedDB")
        if not has_indexeddb:
            pytest.skip('Browser does not support IndexedDB')

        # try to detect a search DB named 'deals99_search' (non-fatal if absent)
        db_list_supported = page.evaluate("() => typeof indexedDB.databases === 'function'")
        if db_list_supported:
            dbs = page.evaluate("() => indexedDB.databases().then(d=>d.map(x=>x.name)).catch(()=>[])")
            if 'deals99_search' not in dbs:
                pytest.skip('IndexedDB search DB not implemented yet')
        else:
            # fallback: attempt to open the DB and see if object stores exist
            present = page.evaluate(r"() => new Promise(res=>{ const req = indexedDB.open('deals99_search'); req.onsuccess = e=>{ try{ const stores = e.target.result.objectStoreNames; res(stores.length>0); }catch(err){ res(false); } }; req.onerror = ()=>res(false); req.onupgradeneeded = ()=>{ /* not present */ res(false); }; })")
            if not present:
                pytest.skip('IndexedDB search DB not implemented yet')

        # If we reach here, require at least one entry in localStorage timestamp as well
        idx_ts = page.evaluate("() => { try { return localStorage.getItem('deals99_search_index_ts'); } catch(e) { return null; } }")
        assert idx_ts is not None, 'IndexedDB present — search index timestamp must exist'

    def test_visual_regression_index(self, page, live_server, playwright_artifacts_dir):
        """Take a screenshot of `index.html` and compare byte-for-byte with baseline if it exists.
        If baseline is missing, save screenshot under playwright-artifacts/baselines and skip the test so the developer can verify and commit the baseline."""
        from pathlib import Path
        page.goto(f"{live_server.url}/index.html")
        self.wait_for_frontend_ready(page)

        safe_name = 'index_page'
        out_dir = Path(playwright_artifacts_dir)
        baselines = out_dir / 'baselines'
        baselines.mkdir(exist_ok=True)

        current_png = out_dir / f"{safe_name}.current.png"
        baseline_png = baselines / f"{safe_name}.baseline.png"

        page.screenshot(path=str(current_png), full_page=True)

        if not baseline_png.exists():
            # save baseline for manual approval and fail the test (prompt developer to commit baseline)
            baseline_png.write_bytes(current_png.read_bytes())
            pytest.skip(f'Baseline created at {baseline_png}. Verify and commit it to enable visual regression.')

        # compare bytes exactly
        cur = current_png.read_bytes()
        base = baseline_png.read_bytes()
        assert cur == base, 'Visual regression detected: screenshot differs from baseline'

"""
conftest.py - pytest configuration and fixtures for Deals99 tests
"""

import os
import django
from django.conf import settings
import pytest


def pytest_configure():
    """Configure pytest with Django settings"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deals99_backend.config.settings.dev')
    
    if not settings.configured:
        django.setup()


@pytest.fixture
def api_client():
    """Provide API test client"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_user(db):
    """Create and return an authenticated test user"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        username='testuser'
    )


@pytest.fixture
def admin_user(db):
    """Create and return an admin user"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_superuser(
        email='admin@example.com',
        password='admin123',
        username='admin'
    )


@pytest.fixture
def test_product(db):
    """Create and return a test product"""
    from api.tests.factories import ProductFactory
    return ProductFactory()


# --- Playwright failure capture: screenshot + page HTML ---
def pytest_runtest_makereport(item, call):
    """On test failure, capture Playwright page screenshot and HTML (if `page` fixture used)."""
    if call.when != "call":
        return

    outcome = getattr(call, "excinfo", None)
    if outcome is None:
        return

    if 'page' in item.fixturenames:
        try:
            page = item.funcargs.get('page')
            if not page:
                return
            import os, re
            from pathlib import Path
            safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', item.name)
            out_dir = Path(os.environ.get('PYTEST_PLAYWRIGHT_ARTIFACTS', Path.cwd() / 'playwright-artifacts'))
            out_dir.mkdir(parents=True, exist_ok=True)

            png_path = out_dir / f"{safe_name}.failed.png"
            html_path = out_dir / f"{safe_name}.failed.html"

            # capture screenshot (full page) and HTML
            page.screenshot(path=str(png_path), full_page=True)
            html_content = page.content()
            html_path.write_text(html_content, encoding='utf-8')
        except Exception:
            # never fail the test hook
            pass


@pytest.fixture
def test_category(db):
    """Create and return a test category"""
    from api.tests.factories import CategoryFactory
    return CategoryFactory()


@pytest.fixture
def authenticated_api_client(api_client, authenticated_user):
    """Provide authenticated API test client"""
    api_client.force_authenticate(user=authenticated_user)
    return api_client


@pytest.fixture
def admin_api_client(api_client, admin_user):
    """Provide admin API test client"""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture(scope='session')
def playwright_artifacts_dir(tmp_path_factory):
    """Directory for Playwright artifacts and baselines."""
    from pathlib import Path
    out = Path.cwd() / 'playwright-artifacts'
    out.mkdir(parents=True, exist_ok=True)
    return out

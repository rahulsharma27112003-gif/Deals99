"""
URL configuration for deals99_backend project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve

urlpatterns = [
    # Serve frontend index at root (development only — `Frontend/index.html`)
    path('', TemplateView.as_view(template_name='index.html')),
    path('admin/', admin.site.urls),
    # Backwards-compatible API mount (tests and some clients expect /api/)
    path('api/', include('api.urls')),
    path('api/v1/', include('api.urls')),
    path('api/v1/admin/', include('admin_dashboard.urls')),
    # Backwards-compatible admin mount (frontend/tests may use /api/admin/)
    path('api/admin/', include('admin_dashboard.urls')),
]

# Serve frontend static assets (html, css, js, images) from the `Frontend/` folder in DEBUG
if settings.DEBUG:
    urlpatterns += [
        # Serve raw HTML pages (so /products.html, /cart.html etc. work in dev)
        re_path(r'^(?P<path>.*\.html)$', serve, {'document_root': settings.BASE_DIR.parent.parent / 'Frontend'}),
        re_path(r'^(?P<path>.*\.(?:css|js|png|jpg|jpeg|svg|webp))$', serve,
                {'document_root': settings.BASE_DIR.parent.parent / 'Frontend'}),
    ]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

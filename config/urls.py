"""
URL configuration for haleway project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('apps.core.urls')),  # Homepage and core views
    path('admin/', admin.site.urls),
    path('health/', include('health_check.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('families/', include('apps.families.urls')),  # Family management
    path('trips/', include('apps.trips.urls')),  # Trip management
    path('notes/', include('apps.notes.urls')),  # Note management
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Add browser auto-reload (only if installed and in INSTALLED_APPS)
    if 'django_browser_reload' in settings.INSTALLED_APPS:
        try:
            urlpatterns += [path('__reload__/', include('django_browser_reload.urls'))]
        except Exception:
            pass

    # Add debug toolbar (only if installed and in INSTALLED_APPS)
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        try:
            import debug_toolbar
            urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
        except Exception:
            pass

# ⚠️ IMPORTANT: URL Configuration Required

After running `django-admin startproject config .`, you need to add these URLs to `config/urls.py`:

## Required URLs

Add these imports and URL patterns to your `config/urls.py` file:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Health check endpoints (for Docker, k8s, monitoring)
    path('health/', include('health_check.urls')),

    # Your app URLs
    # path('', include('apps.core.urls')),  # Add your app URLs here
]

# Development-only URLs
if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        # Django Debug Toolbar
        path('__debug__/', include(debug_toolbar.urls)),

        # Browser auto-reload (saves you from manual refreshes!)
        path('__reload__/', include('django_browser_reload.urls')),
    ]

    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## Why These URLs?

1. **`/health/`** - Health check endpoint for:
   - Docker health checks
   - Kubernetes liveness/readiness probes
   - Uptime monitoring services
   - Load balancer health checks

2. **`/__reload__/`** - Browser auto-reload:
   - Automatically refreshes your browser when you save code
   - HUGE productivity boost during development
   - Only enabled in DEBUG mode

3. **`/__debug__/`** - Django Debug Toolbar:
   - Shows SQL queries, performance metrics
   - Only enabled in DEBUG mode

## Testing Health Checks

After adding the URLs and starting your server:

```bash
# Start development server
make run

# In another terminal, test health endpoint
make health
# or
curl http://localhost:8000/health/
```

## Delete This File

Once you've added these URLs to `config/urls.py`, you can delete this reminder file!

---

**📝 Note**: These URLs are documented in:
- `CLAUDE.md` - AI assistant reference
- `docs/SETUP_GUIDE.md` - Complete setup documentation

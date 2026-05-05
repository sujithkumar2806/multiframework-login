from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def metrics_view(request):
    # Simple metrics for Django to make Prometheus happy
    metrics_data = '''# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{framework="django",method="GET",endpoint="/api/health"} 0
# HELP up Was the last scrape of Django successful
# TYPE up gauge
up{job="django-backend"} 1
'''
    return HttpResponse(metrics_data, content_type="text/plain")

def health_view(request):
    return HttpResponse('{"status": "healthy", "framework": "Django 🚀"}', content_type="application/json")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('metrics', metrics_view, name='metrics'),
    path('api/health', health_view, name='health'),
]
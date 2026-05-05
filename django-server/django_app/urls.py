from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from datetime import datetime

# Initialize counters
request_count_fastapi = 0
request_count_django = 0
request_count_node = 0
request_count_dotnet = 0

def metrics_view(request):
    global request_count_django
    metrics_data = f'''# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{{framework="fastapi"}} {request_count_fastapi}
http_requests_total{{framework="django"}} {request_count_django}
http_requests_total{{framework="node"}} {request_count_node}
http_requests_total{{framework="dotnet"}} {request_count_dotnet}
# HELP up Was the last scrape successful
# TYPE up gauge
up{{job="django-backend"}} 1
'''
    return HttpResponse(metrics_data, content_type="text/plain")

def health_view(request):
    global request_count_django
    request_count_django += 1
    return HttpResponse('{"status": "healthy", "framework": "Django 🚀"}', content_type="application/json")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('metrics', metrics_view, name='metrics'),
    path('api/health', health_view, name='health'),
]
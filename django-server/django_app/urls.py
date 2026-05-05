from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Use a simple integer that we'll update
counter = 0

def metrics_view(request):
    global counter
    metrics_data = f'''# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{{framework="django"}} {counter}
# HELP up Was the last scrape of Django successful
# TYPE up gauge
up{{job="django-backend"}} 1
'''
    return HttpResponse(metrics_data, content_type="text/plain")

@csrf_exempt
def health_view(request):
    global counter
    counter += 1
    print(f"Health check called! Counter is now: {counter}")  # Debug log
    return HttpResponse('{"status": "healthy", "framework": "Django 🚀"}', content_type="application/json")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('metrics', metrics_view, name='metrics'),
    path('api/health', health_view, name='health'),
]
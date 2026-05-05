from django.http import HttpResponse
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
    path('metrics', metrics_view),
]
def metrics_view(request):
    return HttpResponse("# No metrics yet\n", content_type="text/plain")
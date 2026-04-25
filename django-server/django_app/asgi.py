import os
import sys

# Add the parent directory to Python path
sys.path.append('/app')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')

from django.core.asgi import get_asgi_application
application = get_asgi_application()

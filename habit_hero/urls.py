from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views as drf_auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # token login: POST username & password -> { "token": "..." }
    path('api/login/', drf_auth_views.obtain_auth_token, name='api-token-auth'),
    path('api/', include('habit_app.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

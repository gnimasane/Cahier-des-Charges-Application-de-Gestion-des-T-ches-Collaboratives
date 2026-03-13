from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Templates (Objectif 1)
    path('', include('users.urls')),
    path('projects/', include('projects.urls')),
    path('tasks/', include('tasks.urls')),
    # API REST (Objectif 2 - Angular)
    path('api/', include('esmt_backend.api_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

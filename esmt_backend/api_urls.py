from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/', include('users.api_urls')),
    path('projects/', include('projects.api_urls')),
    path('tasks/', include('tasks.api_urls')),
    path('statistics/', include('statistics_app.api_urls')),
]

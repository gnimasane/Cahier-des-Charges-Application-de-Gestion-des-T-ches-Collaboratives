from django.urls import path
from .api_views import RegisterAPIView, LoginAPIView, ProfileAPIView, ChangePasswordAPIView, UserListAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='api-register'),
    path('login/', LoginAPIView.as_view(), name='api-login'),
    path('profile/', ProfileAPIView.as_view(), name='api-profile'),
    path('change-password/', ChangePasswordAPIView.as_view(), name='api-change-password'),
    path('', UserListAPIView.as_view(), name='api-users'),
]

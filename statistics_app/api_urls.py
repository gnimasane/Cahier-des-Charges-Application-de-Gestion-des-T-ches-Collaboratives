from django.urls import path
from .api_views import MyStatsAPIView, TeamStatsAPIView, DashboardStatsAPIView

urlpatterns = [
    path('me/', MyStatsAPIView.as_view(), name='api-my-stats'),
    path('team/', TeamStatsAPIView.as_view(), name='api-team-stats'),
    path('dashboard/', DashboardStatsAPIView.as_view(), name='api-dashboard-stats'),
]

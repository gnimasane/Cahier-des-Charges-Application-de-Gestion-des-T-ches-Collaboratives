from django.urls import path
from .api_views import ProjectListCreateAPIView, ProjectDetailAPIView, ProjectMembersAPIView

urlpatterns = [
    path('', ProjectListCreateAPIView.as_view(), name='api-projects'),
    path('<int:pk>/', ProjectDetailAPIView.as_view(), name='api-project-detail'),
    path('<int:pk>/members/', ProjectMembersAPIView.as_view(), name='api-project-members'),
]

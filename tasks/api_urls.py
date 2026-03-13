from django.urls import path
from .api_views import TaskListCreateAPIView, TaskDetailAPIView, AssignableUsersAPIView

urlpatterns = [
    path('', TaskListCreateAPIView.as_view(), name='api-tasks-list'),
    path('<int:pk>/', TaskDetailAPIView.as_view(), name='api-task-detail'),
    path('assignable/<int:project_id>/', AssignableUsersAPIView.as_view(), name='api-assignable-users'),
]

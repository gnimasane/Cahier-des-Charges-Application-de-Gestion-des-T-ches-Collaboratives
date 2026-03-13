from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list_view, name='task-list'),
    path('project/<int:project_id>/create/', views.task_create_view, name='task-create'),
    path('<int:pk>/', views.task_detail_view, name='task-detail'),
    path('<int:pk>/edit/', views.task_edit_view, name='task-edit'),
    path('<int:pk>/delete/', views.task_delete_view, name='task-delete'),
]

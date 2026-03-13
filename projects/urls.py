from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list_view, name='project-list'),
    path('create/', views.project_create_view, name='project-create'),
    path('<int:pk>/', views.project_detail_view, name='project-detail'),
    path('<int:pk>/edit/', views.project_edit_view, name='project-edit'),
    path('<int:pk>/delete/', views.project_delete_view, name='project-delete'),
]

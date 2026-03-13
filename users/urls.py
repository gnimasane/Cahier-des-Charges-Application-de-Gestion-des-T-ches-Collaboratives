from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('dashboard/professeur/', views.dashboard_professeur_view, name='dashboard-professeur'),
    path('dashboard/etudiant/', views.dashboard_etudiant_view, name='dashboard-etudiant'),
]

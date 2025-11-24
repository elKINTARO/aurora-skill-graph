from django.urls import path
from . import views

urlpatterns = [
    path('', views.skill_list, name='skill_list'),
    path('skill/new/', views.skill_create, name='skill_create'),
    path('skill/<slug:skill_slug>/', views.skill_detail, name='skill_detail'),
    path('skill/<slug:skill_slug>/change/<str:new_status>/', views.change_status, name='change_status'),
    path('register/', views.register, name='register'),
    path('profile/', views.user_profile, name='profile'),
]
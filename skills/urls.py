from django.urls import path
from . import views

urlpatterns = [
    path('', views.skill_list, name='skill_list'),
    path('skill/new/', views.skill_create, name='skill_create'),
    path('skill/<slug:skill_slug>/', views.skill_detail, name='skill_detail'),
    path('skill/<slug:skill_slug>/edit/', views.skill_edit, name='skill_edit'),
    path('skill/<slug:skill_slug>/delete/', views.skill_delete, name='skill_delete'),
    path('skill/<slug:skill_slug>/change/<str:new_status>/', views.change_status, name='change_status'),
    path('skill/<slug:skill_slug>/add-dependency/', views.skill_add_dependency, name='add_dependency'),
    path('skill/<slug:skill_slug>/remove-dependency/<int:dependency_id>/', views.skill_remove_dependency,
         name='remove_dependency'),
    path('register/', views.register, name='register'),
    path('profile/', views.user_profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('ai-generator/', views.ai_generator, name='ai_generator'),
]
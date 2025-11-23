from django.urls import path
from . import views

urlpatterns = [
    path('', views.skill_list, name='skill_list'),
    path('skill/<slug:skill_slug>/change/<str:new_status>/', views.change_status, name='change_status'),
]
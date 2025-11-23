from django.urls import path
from . import views

urlpatterns = [
    path('', views.skill_list, name='skill_list'),
]
from django.urls import path 
from . import views

urlpatterns = [
    path('api/tasks/analyze/', views),
    path('api/tasks/suggest', views),
]



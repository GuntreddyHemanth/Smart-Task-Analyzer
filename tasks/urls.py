from django.urls import path
from . import views

urlpatterns = [
    path('api/tasks/analyze/', views.analyze_tasks, name='analyze_tasks'),
    path('api/tasks/suggest/', views.suggest_tasks, name='suggest_tasks'),
    path('', views.index, name='index'),
]



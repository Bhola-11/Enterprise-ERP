from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_dashboard, name='dashboard'),
    path('list/', views.project_list, name='project_list'),
    path('add/', views.project_create, name='project_create'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('tasks/<int:pk>/status/', views.task_status_update, name='task_status_update'),
    path('timesheets/', views.timesheet_list, name='timesheet_list'),
]

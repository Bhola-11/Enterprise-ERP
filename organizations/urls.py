from django.urls import path
from . import views

app_name = 'organizations'

urlpatterns = [
    path('settings/', views.organization_settings, name='settings'),
    path('branches/add/', views.branch_create_or_edit, name='branch_create'),
    path('branches/<int:branch_id>/edit/', views.branch_create_or_edit, name='branch_edit'),
    path('departments/add/', views.department_create_or_edit, name='department_create'),
    path('departments/<int:dept_id>/edit/', views.department_create_or_edit, name='department_edit'),
]

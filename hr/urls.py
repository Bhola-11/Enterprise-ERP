from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    path('', views.hr_dashboard, name='dashboard'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('org-chart/', views.org_chart_view, name='org_chart'),
    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/apply/', views.leave_request_create, name='leave_apply'),
    path('attendance/', views.attendance_list, name='attendance_list'),
]

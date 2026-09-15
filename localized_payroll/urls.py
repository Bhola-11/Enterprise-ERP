from django.urls import path
from . import views

app_name = 'localized_payroll'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('payruns/', views.payrun_list, name='payrun_list'),
    path('payruns/create/', views.payrun_create, name='payrun_create'),
    path('payruns/<int:pk>/', views.payrun_detail, name='payrun_detail'),
    path('payslips/<int:pk>/', views.payslip_detail, name='payslip_detail'),
    path('salaries/', views.salary_list, name='salary_list'),
    path('salaries/create/', views.salary_create, name='salary_create'),
    path('jurisdictions/', views.jurisdictions_list, name='jurisdictions_list'),
]

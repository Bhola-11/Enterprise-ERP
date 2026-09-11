from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.payroll_dashboard, name='dashboard'),
    path('generate/', views.payrun_generate, name='generate'),
    path('payruns/<int:pk>/', views.payrun_detail, name='payrun_detail'),
    path('payslips/<int:pk>/', views.payslip_detail, name='payslip_detail'),
]

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_center, name='center'),
    path('sales/', views.sales_report, name='sales'),
    path('inventory/', views.inventory_report, name='inventory'),
    path('financial/', views.financial_report, name='financial'),
]

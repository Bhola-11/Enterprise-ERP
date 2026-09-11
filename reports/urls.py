from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_center, name='report_center'),
    path('center/', views.report_center, name='center'),
    path('sales/', views.sales_report, name='sales_report'),
    path('sales-summary/', views.sales_report, name='sales'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('inventory-summary/', views.inventory_report, name='inventory'),
    path('financial/', views.financial_report, name='financial_report'),
    path('financial-summary/', views.financial_report, name='financial'),
]

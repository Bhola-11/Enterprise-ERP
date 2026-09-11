from django.urls import path
from . import views

app_name = 'taxation'

urlpatterns = [
    path('', views.tax_dashboard, name='dashboard'),
    path('jurisdictions/', views.jurisdiction_list, name='jurisdiction_list'),
    path('jurisdictions/create/', views.jurisdiction_create, name='jurisdiction_create'),

    path('hsn/', views.hsn_list, name='hsn_list'),
    path('hsn/create/', views.hsn_create, name='hsn_create'),

    path('eway-bills/', views.eway_bill_list, name='eway_bill_list'),
    path('eway-bills/create/', views.eway_bill_create, name='eway_bill_create'),
    path('eway-bills/<int:pk>/', views.eway_bill_detail, name='eway_bill_detail'),

    path('einvoices/', views.einvoice_list, name='einvoice_list'),
    path('einvoices/<int:pk>/', views.einvoice_detail, name='einvoice_detail'),

    path('filings/', views.tax_filing_list, name='tax_filing_list'),
    path('filings/create/', views.tax_filing_create, name='tax_filing_create'),
    path('reports/gstr1/', views.gstr1_generator, name='gstr1_report'),

    # Real-time API
    path('api/calculate/', views.api_calculate_tax, name='api_calculate_tax'),
]

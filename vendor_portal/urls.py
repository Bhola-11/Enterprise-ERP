from django.urls import path
from . import views

app_name = 'vendor_portal'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('rfqs/', views.rfq_list_view, name='rfq_list'),
    path('rfqs/<int:pk>/bid/', views.bid_submit_view, name='bid_submit'),
    path('asns/', views.asn_list_view, name='asn_list'),
    path('asns/new/', views.asn_create_view, name='asn_create'),
    path('invoices/', views.invoice_list_view, name='invoice_list'),
    path('invoices/upload/', views.invoice_upload_view, name='invoice_upload'),
    path('three-way-match/', views.three_way_match_view, name='three_way_match'),
]

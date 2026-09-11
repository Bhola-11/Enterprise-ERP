from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('', views.crm_dashboard, name='dashboard'),
    path('pipeline/', views.pipeline_view, name='pipeline'),
    path('leads/', views.lead_list, name='lead_list'),
    path('leads/add/', views.lead_create, name='lead_create'),
    path('leads/<int:pk>/', views.lead_detail, name='lead_detail'),
    path('leads/<int:pk>/convert/', views.lead_convert, name='lead_convert'),
    path('opportunities/add/', views.opportunity_create, name='opportunity_create'),
    path('contacts/', views.contact_list, name='contact_list'),
    path('companies/', views.company_list, name='company_list'),
]

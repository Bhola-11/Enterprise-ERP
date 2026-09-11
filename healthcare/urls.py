from django.urls import path
from . import views

app_name = 'healthcare'

urlpatterns = [
    path('', views.healthcare_dashboard, name='dashboard'),

    # Patients & EMR Charts
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/create/', views.patient_create, name='patient_create'),
    path('patients/<int:pk>/', views.patient_detail, name='patient_detail'),

    # OPD Scheduling & Consultations
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/book/', views.appointment_book, name='appointment_book'),
    path('appointments/<int:appointment_id>/consult/', views.consultation_create, name='consultation_create'),

    # Pathology & Lab Orders
    path('labs/', views.lab_order_list, name='lab_order_list'),
    path('labs/order/', views.lab_order_create, name='lab_order_create'),

    # Inpatient Admissions (IPD)
    path('inpatient/', views.inpatient_list, name='inpatient_list'),
    path('inpatient/admit/', views.inpatient_admit, name='inpatient_admit'),

    # Billing & Claims
    path('billing/', views.billing_list, name='billing_list'),
    path('patients/<int:patient_id>/generate-bill/', views.billing_generate, name='billing_generate'),

    # Clinical APIs
    path('api/vitals/assess/', views.api_vital_signs_assess, name='api_vital_signs_assess'),
    path('api/drugs/check-allergy/', views.api_check_drug_allergy, name='api_check_drug_allergy'),
]

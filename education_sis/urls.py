from django.urls import path
from . import views

app_name = 'education_sis'

urlpatterns = [
    path('', views.sis_dashboard, name='dashboard'),
    path('students/', views.student_list, name='student_list'),
    path('students/create/', views.student_create, name='student_create'),
    path('students/<int:pk>/', views.student_profile, name='student_profile'),
    path('courses/', views.course_list, name='course_list'),
    path('fees/', views.fee_invoice_list, name='fee_invoice_list'),
    path('fees/<int:pk>/pay/', views.fee_payment_process, name='fee_payment_process'),
    path('gradebook/', views.grade_book, name='grade_book'),
]

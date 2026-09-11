from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_vault, name='vault'),
    path('upload/', views.document_upload, name='upload'),
    path('folders/add/', views.folder_create, name='folder_create'),
]

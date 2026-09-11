from django.urls import path
from . import views

app_name = 'hospitality_pms'

urlpatterns = [
    path('', views.hospitality_dashboard, name='dashboard'),
    path('rack/', views.room_matrix, name='room_matrix'),
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('reservations/create/', views.reservation_create, name='reservation_create'),
    path('reservations/<int:pk>/', views.reservation_detail, name='reservation_detail'),
    path('reservations/<int:pk>/check-in/', views.check_in_guest, name='check_in'),
    path('reservations/<int:pk>/check-out/', views.check_out_guest, name='check_out'),
    path('reservations/<int:pk>/charge/', views.add_folio_charge, name='add_folio_charge'),
    path('housekeeping/', views.housekeeping_board, name='housekeeping_board'),
]

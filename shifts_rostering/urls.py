from django.urls import path
from . import views

app_name = 'shifts_rostering'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('roster/', views.roster_calendar, name='roster_calendar'),
    path('roster/assign/', views.roster_assign, name='roster_assign'),
    path('shifts/', views.shift_list, name='shift_list'),
    path('shifts/create/', views.shift_create, name='shift_create'),
    path('punch/', views.punch_portal, name='punch_portal'),
    path('timesheets/', views.timesheet_summary, name='timesheet_summary'),
]

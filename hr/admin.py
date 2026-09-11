from django.contrib import admin
from .models import Designation, Employee, Attendance, LeaveType, LeaveRequest, Holiday

@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'department')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'email', 'department', 'designation', 'status', 'joining_date')
    list_filter = ('department', 'status', 'branch')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'check_in', 'check_out', 'status', 'work_hours')
    list_filter = ('status', 'date')

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'days_allowed_per_year', 'is_paid')

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'total_days', 'status')
    list_filter = ('status', 'leave_type')

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date')

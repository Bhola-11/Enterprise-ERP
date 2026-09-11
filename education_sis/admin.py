from django.contrib import admin
from .models import (
    DepartmentFaculty, AcademicProgram, AcademicSession, StudentProfile,
    CourseModule, CourseEnrollment, FeeStructure, StudentFeeInvoice,
    ExamSchedule, StudentGradeResult
)

@admin.register(DepartmentFaculty)
class DepartmentFacultyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'dean_name', 'email', 'building_location')
    search_fields = ('code', 'name')

@admin.register(AcademicProgram)
class AcademicProgramAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'degree_level', 'tuition_per_semester')
    list_filter = ('degree_level', 'department')

@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'term', 'start_date', 'end_date', 'is_active')
    list_filter = ('term', 'is_active')

class CourseEnrollmentInline(admin.TabularInline):
    model = CourseEnrollment
    extra = 1

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'first_name', 'last_name', 'program', 'current_semester', 'academic_status', 'current_gpa')
    search_fields = ('student_id', 'first_name', 'last_name', 'email')
    list_filter = ('academic_status', 'program', 'current_semester')
    inlines = [CourseEnrollmentInline]

@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'program', 'credits', 'semester_recommended', 'is_elective')
    list_filter = ('program', 'semester_recommended', 'is_elective')

@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'session', 'final_grade_letter', 'grade_point', 'attendance_percentage', 'status')
    list_filter = ('status', 'session')

@admin.register(StudentFeeInvoice)
class StudentFeeInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'student', 'session', 'total_amount', 'paid_amount', 'balance_amount', 'status', 'due_date')
    list_filter = ('status', 'session')

from django import forms
from .models import (
    StudentProfile, AcademicProgram, DepartmentFaculty, CourseModule,
    CourseEnrollment, AcademicSession, StudentGradeResult, StudentFeeInvoice
)

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            'student_id', 'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'gender', 'program', 'current_semester',
            'admission_date', 'academic_status', 'guardian_name', 'guardian_phone', 'address'
        ]
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'program': forms.Select(attrs={'class': 'form-select'}),
            'current_semester': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
            'admission_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'academic_status': forms.Select(attrs={'class': 'form-select'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class CourseModuleForm(forms.ModelForm):
    class Meta:
        model = CourseModule
        fields = ['program', 'code', 'title', 'credits', 'semester_recommended', 'syllabus_summary', 'is_elective']
        widgets = {
            'program': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control'}),
            'semester_recommended': forms.NumberInput(attrs={'class': 'form-control'}),
            'syllabus_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_elective': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CourseEnrollmentForm(forms.ModelForm):
    class Meta:
        model = CourseEnrollment
        fields = ['student', 'course', 'session', 'status', 'final_grade_letter', 'grade_point', 'attendance_percentage']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'session': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'final_grade_letter': forms.TextInput(attrs={'class': 'form-control'}),
            'grade_point': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'attendance_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }


class FeePaymentForm(forms.Form):
    payment_amount = forms.DecimalField(max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    payment_method = forms.ChoiceField(choices=[('ONLINE', 'Online Portal / Card'), ('BANK_TRANSFER', 'Bank Wire Transfer'), ('CASH', 'Cash Counter'), ('CHEQUE', 'Cheque')], widget=forms.Select(attrs={'class': 'form-select'}))
    reference_number = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TXN-998822'}))

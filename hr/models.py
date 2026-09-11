from django.db import models
from django.conf import settings
from organizations.models import Department, Branch

class Designation(models.Model):
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='designations')

    def __str__(self):
        return f"{self.title} ({self.department.name})"

class Employee(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    STATUS_CHOICES = [
        ('ACTIVE', 'Active Full-Time'),
        ('PROBATION', 'Probationary'),
        ('ON_LEAVE', 'On Extended Leave'),
        ('TERMINATED', 'Terminated / Resigned'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_profile')
    employee_id = models.CharField(max_length=30, unique=True) # e.g. NX-EMP-1001
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='employees')
    designation = models.ForeignKey(Designation, on_delete=models.PROTECT, related_name='employees')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='employees')
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_reports')
    joining_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True, null=True)
    avatar = models.ImageField(upload_to='employees/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f"[{self.employee_id}] {self.first_name} {self.last_name} ({self.designation.title})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('HALF_DAY', 'Half Day'),
        ('ON_LEAVE', 'On Approved Leave'),
        ('WFH', 'Work From Home'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')
    work_hours = models.DecimalField(max_digits=4, decimal_places=2, default=8.00)
    notes = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.date} ({self.get_status_display()})"

class LeaveType(models.Model):
    name = models.CharField(max_length=100) # Annual Leave, Sick Leave, Maternity Leave
    code = models.CharField(max_length=20, unique=True)
    days_allowed_per_year = models.PositiveSmallIntegerField(default=14)
    is_paid = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.days_allowed_per_year} days)"

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Manager Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.PositiveSmallIntegerField(default=1)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name} ({self.total_days} days)"

class Holiday(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField(unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.name} ({self.date})"

from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from hr.models import Employee, Department

class ShiftTemplate(models.Model):
    name = models.CharField(max_length=100)
    shift_code = models.CharField(max_length=30, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_duration_minutes = models.PositiveIntegerField(default=45)
    grace_period_minutes = models.PositiveIntegerField(default=15)
    is_night_shift = models.BooleanField(default=False)
    hourly_rate_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('1.00'))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['start_time']
        verbose_name = 'Shift Template'
        verbose_name_plural = 'Shift Templates'

    def __str__(self):
        return f"{self.shift_code}: {self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"


class ShiftRosterAssignment(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('CONFIRMED', 'Confirmed by Employee'),
        ('SWAPPED', 'Shift Swapped'),
        ('CANCELLED', 'Cancelled / Leave Off'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='roster_assignments')
    shift_template = models.ForeignKey(ShiftTemplate, on_delete=models.PROTECT, related_name='assigned_rosters')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['date', 'employee']
        verbose_name = 'Shift Roster Assignment'
        verbose_name_plural = 'Shift Roster Assignments'

    def __str__(self):
        return f"{self.employee} @ {self.date}: {self.shift_template.name}"


class BiometricPunchLog(models.Model):
    PUNCH_TYPES = [
        ('CLOCK_IN', 'Clock In (Shift Start)'),
        ('CLOCK_OUT', 'Clock Out (Shift End)'),
        ('BREAK_START', 'Meal / Rest Break Start'),
        ('BREAK_END', 'Meal / Rest Break Return'),
    ]
    VERIFICATION_METHODS = [
        ('FACIAL_RECOGNITION', 'AI Facial Recognition Biometric Terminal'),
        ('FINGERPRINT', 'Optical Fingerprint Scanner'),
        ('RFID_BADGE', 'NFC / RFID Security Badge'),
        ('MOBILE_GPS', 'Mobile App Geo-Fenced Punch'),
        ('MANUAL_HR', 'HR Manual Override Approval'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='biometric_punches')
    punch_time = models.DateTimeField(default=timezone.now)
    punch_type = models.CharField(max_length=20, choices=PUNCH_TYPES, default='CLOCK_IN')
    device_terminal_id = models.CharField(max_length=50, default='TERM-MAIN-01')
    verification_method = models.CharField(max_length=30, choices=VERIFICATION_METHODS, default='FACIAL_RECOGNITION')
    is_manual_override = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-punch_time']
        verbose_name = 'Biometric Punch Log'
        verbose_name_plural = 'Biometric Punch Logs'

    def __str__(self):
        return f"{self.employee} - {self.get_punch_type_display()} @ {self.punch_time.strftime('%Y-%m-%d %H:%M:%S')}"


class AttendanceSummaryPeriod(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'On Time / Normal Shift'),
        ('LATE', 'Tardy / Late Arrival'),
        ('EARLY_DEPARTURE', 'Early Departure'),
        ('ABSENT', 'Unexcused Absence'),
        ('ON_LEAVE', 'Approved Paid Leave'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='daily_attendance_summaries')
    date = models.DateField()
    shift_template = models.ForeignKey(ShiftTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    clock_in_time = models.DateTimeField(null=True, blank=True)
    clock_out_time = models.DateTimeField(null=True, blank=True)

    scheduled_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('8.00'))
    regular_hours_worked = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    overtime_1_5x_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    overtime_2_0x_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    late_minutes = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date', 'employee']
        verbose_name = 'Daily Timesheet & Overtime Summary'
        verbose_name_plural = 'Daily Timesheet & Overtime Summaries'

    def __str__(self):
        return f"{self.employee} @ {self.date}: {self.regular_hours_worked}h Reg + {self.overtime_1_5x_hours}h OT ({self.status})"

    @property
    def total_hours_worked(self):
        return self.regular_hours_worked + self.overtime_1_5x_hours + self.overtime_2_0x_hours

from decimal import Decimal
from datetime import date, time, datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from hr.models import Employee, Department, Designation
from organizations.models import Organization, Branch
from shifts_rostering.models import ShiftTemplate, ShiftRosterAssignment, BiometricPunchLog, AttendanceSummaryPeriod
from shifts_rostering.services import OvertimeCalculationEngine, RosterConflictChecker

User = get_user_model()

class ShiftsRosteringTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='shift_admin',
            email='shifts@nexora.io',
            password='Password123!'
        )
        self.org = Organization.objects.create(name='Nexora Manufacturing', currency='USD')
        self.branch = Branch.objects.create(organization=self.org, name='Detroit Hub', code='HUB-DET')
        self.dept = Department.objects.create(organization=self.org, name='Plant Robotics', code='ROB', branch=self.branch)
        self.des_tech = Designation.objects.create(title='Robotics Technician', code='DES-ROB-01', department=self.dept)

        self.emp = Employee.objects.create(
            employee_id='EMP-SR-001', first_name='Lucas', last_name='Muller',
            email='l.muller@nexora.io', department=self.dept, designation=self.des_tech,
            branch=self.branch, joining_date=date(2023, 1, 1), status='ACTIVE'
        )

        self.shift_morning = ShiftTemplate.objects.create(
            name='Alpha Morning Shift',
            shift_code='SHIFT-AM-01',
            start_time=time(8, 0),
            end_time=time(16, 30),
            break_duration_minutes=30,
            grace_period_minutes=15
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_roster_conflict_checker(self):
        target_date = date(2026, 3, 16)
        ShiftRosterAssignment.objects.create(
            employee=self.emp,
            shift_template=self.shift_morning,
            date=target_date
        )

        is_valid, msg = RosterConflictChecker.validate_assignment(self.emp, target_date, self.shift_morning)
        self.assertFalse(is_valid)
        self.assertIn("already scheduled", msg)

    def test_overtime_calculation_engine(self):
        target_date = date(2026, 3, 16)
        ShiftRosterAssignment.objects.create(
            employee=self.emp,
            shift_template=self.shift_morning,
            date=target_date
        )

        # Clock in at 08:00, clock out at 19:00 (11h total - 30m break = 10.5h -> 8.0h reg + 2.5h OT 1.5x)
        tz = timezone.get_current_timezone()
        dt_in = timezone.make_aware(datetime.combine(target_date, time(8, 0)), tz)
        dt_out = timezone.make_aware(datetime.combine(target_date, time(19, 0)), tz)

        BiometricPunchLog.objects.create(
            employee=self.emp,
            punch_time=dt_in,
            punch_type='CLOCK_IN',
            verification_method='FACIAL_RECOGNITION'
        )
        BiometricPunchLog.objects.create(
            employee=self.emp,
            punch_time=dt_out,
            punch_type='CLOCK_OUT',
            verification_method='FACIAL_RECOGNITION'
        )

        summary = OvertimeCalculationEngine.process_daily_timesheet(self.emp, target_date)
        self.assertIsNotNone(summary)
        self.assertEqual(summary.regular_hours_worked, Decimal('8.00'))
        self.assertEqual(summary.overtime_1_5x_hours, Decimal('2.50'))
        self.assertEqual(summary.status, 'PRESENT')

    def test_views(self):
        res_dash = self.client.get(reverse('shifts_rostering:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_cal = self.client.get(reverse('shifts_rostering:roster_calendar'))
        self.assertEqual(res_cal.status_code, 200)

        res_shifts = self.client.get(reverse('shifts_rostering:shift_list'))
        self.assertEqual(res_shifts.status_code, 200)

        res_punch = self.client.get(reverse('shifts_rostering:punch_portal'))
        self.assertEqual(res_punch.status_code, 200)

        res_ts = self.client.get(reverse('shifts_rostering:timesheet_summary'))
        self.assertEqual(res_ts.status_code, 200)

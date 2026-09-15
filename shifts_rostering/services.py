from decimal import Decimal
from datetime import datetime, time, timedelta
from django.utils import timezone
from .models import ShiftTemplate, ShiftRosterAssignment, BiometricPunchLog, AttendanceSummaryPeriod

class OvertimeCalculationEngine:
    @classmethod
    def process_daily_timesheet(cls, employee, target_date):
        """
        Processes biometric in/out logs for an employee on a given date:
        - Calculates total duration worked minus standard break.
        - Splits into Regular (up to 8.0h), Overtime 1.5x (8.0h to 12.0h), and Double Time 2.0x (>12.0h).
        - Computes late arrival minutes compared to roster assignment.
        """
        # 1. Fetch assigned roster shift
        roster = ShiftRosterAssignment.objects.filter(employee=employee, date=target_date).first()
        shift = roster.shift_template if roster else None

        # 2. Fetch biometric punches for date
        punches = BiometricPunchLog.objects.filter(
            employee=employee,
            punch_time__date=target_date
        ).order_by('punch_time')

        first_in = punches.filter(punch_type='CLOCK_IN').first()
        last_out = punches.filter(punch_type='CLOCK_OUT').last()

        scheduled_hrs = Decimal('8.00')
        reg_hrs = Decimal('0.00')
        ot_15_hrs = Decimal('0.00')
        ot_20_hrs = Decimal('0.00')
        late_mins = 0
        status = 'ABSENT'

        in_time = first_in.punch_time if first_in else None
        out_time = last_out.punch_time if last_out else None

        if in_time and out_time and out_time > in_time:
            diff_secs = (out_time - in_time).total_seconds()
            break_secs = (shift.break_duration_minutes * 60) if shift else 2700 # default 45 mins
            net_worked_secs = max(0, diff_secs - break_secs)
            total_worked_hrs = Decimal(str(round(net_worked_secs / 3600.0, 2)))

            # Check late minutes
            if shift:
                expected_start = datetime.combine(target_date, shift.start_time)
                # Convert timezone if needed
                if in_time.tzinfo:
                    in_time_naive = in_time.astimezone(timezone.get_current_timezone()).replace(tzinfo=None)
                else:
                    in_time_naive = in_time

                if in_time_naive > expected_start + timedelta(minutes=shift.grace_period_minutes):
                    late_mins = int((in_time_naive - expected_start).total_seconds() / 60)
                    status = 'LATE'
                else:
                    status = 'PRESENT'
            else:
                status = 'PRESENT'

            # Tiered FLSA / Statutory Overtime Splitting
            if total_worked_hrs <= Decimal('8.00'):
                reg_hrs = total_worked_hrs
            elif total_worked_hrs <= Decimal('12.00'):
                reg_hrs = Decimal('8.00')
                ot_15_hrs = total_worked_hrs - Decimal('8.00')
            else:
                reg_hrs = Decimal('8.00')
                ot_15_hrs = Decimal('4.00')
                ot_20_hrs = total_worked_hrs - Decimal('12.00')

        elif in_time and not out_time:
            reg_hrs = Decimal('4.00')
            status = 'PRESENT'

        summary, _ = AttendanceSummaryPeriod.objects.update_or_create(
            employee=employee,
            date=target_date,
            defaults={
                'shift_template': shift,
                'clock_in_time': in_time,
                'clock_out_time': out_time,
                'scheduled_hours': scheduled_hrs,
                'regular_hours_worked': reg_hrs,
                'overtime_1_5x_hours': ot_15_hrs,
                'overtime_2_0x_hours': ot_20_hrs,
                'late_minutes': late_mins,
                'status': status
            }
        )
        return summary


class RosterConflictChecker:
    @classmethod
    def validate_assignment(cls, employee, assign_date, shift):
        """
        Validates shift assignment against double booking and mandatory rest breaks.
        """
        existing = ShiftRosterAssignment.objects.filter(employee=employee, date=assign_date).exclude(status='CANCELLED').first()
        if existing:
            return False, f"Employee is already scheduled for '{existing.shift_template.name}' on {assign_date}."

        # Check consecutive night shifts or rest periods
        prev_date = assign_date - timedelta(days=1)
        prev_roster = ShiftRosterAssignment.objects.filter(employee=employee, date=prev_date).first()
        if prev_roster and prev_roster.shift_template.is_night_shift and not shift.is_night_shift:
            # Shift turnaround check
            if shift.start_time < time(14, 0):
                return False, f"Mandatory 11-hour rest period violated after previous night shift on {prev_date}."

        return True, "Valid shift assignment."

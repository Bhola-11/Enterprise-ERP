import uuid
from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import DepreciableAsset, AssetDepreciationPeriod, AssetImpairmentRecord, AssetDisposalRecord
from accounting.models import JournalEntry, JournalItem, Account

class DepreciationEngine:
    @classmethod
    def generate_full_schedule(cls, asset):
        """
        Builds complete monthly depreciation schedule from acquisition date through useful life.
        """
        asset.depreciation_schedule.all().delete()

        cost = asset.acquisition_cost
        salvage = asset.salvage_value
        depreciable_base = cost - salvage
        months = asset.useful_life_months
        method = asset.depreciation_method

        curr_nbv = cost
        accum_depr = Decimal('0.00')

        monthly_sl = (depreciable_base / Decimal(str(months))).quantize(Decimal('0.01')) if months > 0 else Decimal('0.00')

        # Generate schedule month by month
        start_date = asset.acquisition_date
        schedule_periods = []

        for m in range(1, months + 1):
            period_date = start_date + timedelta(days=30 * m)
            opening_nbv = curr_nbv

            if method == 'DOUBLE_DECLINING':
                annual_rate = Decimal('2.0') / (Decimal(str(months)) / Decimal('12.0'))
                monthly_rate = annual_rate / Decimal('12.0')
                depr_amt = (curr_nbv * monthly_rate).quantize(Decimal('0.01'))
                depr_amt = min(depr_amt, curr_nbv - salvage)
            else:
                depr_amt = min(monthly_sl, curr_nbv - salvage)

            if depr_amt < Decimal('0.00'):
                depr_amt = Decimal('0.00')

            closing_nbv = opening_nbv - depr_amt
            curr_nbv = closing_nbv
            accum_depr += depr_amt

            p = AssetDepreciationPeriod(
                asset=asset,
                period_date=period_date,
                opening_book_value=opening_nbv,
                depreciation_amount=depr_amt,
                closing_book_value=closing_nbv,
                is_posted=False
            )
            schedule_periods.append(p)

        AssetDepreciationPeriod.objects.bulk_create(schedule_periods)
        asset.net_book_value = cost
        asset.accumulated_depreciation = Decimal('0.00')
        asset.save(update_fields=['net_book_value', 'accumulated_depreciation'])
        return len(schedule_periods)

    @classmethod
    @transaction.atomic
    def post_depreciation_period(cls, period, user=None):
        if period.is_posted:
            return period.journal_entry

        asset = period.asset
        amt = period.depreciation_amount

        if amt > Decimal('0.00') and user:
            je_num = f"JE-DEP-{asset.asset_tag}-{period.period_date.strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            je = JournalEntry.objects.create(
                entry_number=je_num,
                date=period.period_date,
                reference=f"Depreciation: {asset.asset_tag} ({asset.asset_name})",
                narration=f"Monthly depreciation charge for {asset.asset_tag}",
                status='POSTED',
                total_debit=amt,
                total_credit=amt,
                created_by=user
            )
            JournalItem.objects.create(journal_entry=je, account=asset.depreciation_expense_gl_account, debit=amt, credit=Decimal('0.00'), description="Depreciation Expense")
            JournalItem.objects.create(journal_entry=je, account=asset.accumulated_depr_gl_account, debit=Decimal('0.00'), credit=amt, description=f"Accum Depr {asset.asset_tag}")

            period.journal_entry = je

        period.is_posted = True
        period.save(update_fields=['is_posted', 'journal_entry'])

        asset.accumulated_depreciation += amt
        asset.net_book_value = period.closing_book_value
        if asset.net_book_value <= asset.salvage_value:
            asset.status = 'FULLY_DEPRECIATED'
        asset.save(update_fields=['accumulated_depreciation', 'net_book_value', 'status'])

        return period.journal_entry


class AssetImpairmentService:
    @classmethod
    @transaction.atomic
    def record_impairment(cls, asset, recoverable_amt, reason_text, user=None):
        carrying_before = asset.net_book_value
        loss = max(Decimal('0.00'), carrying_before - recoverable_amt)

        je = None
        if loss > 0 and user:
            je = JournalEntry.objects.create(
                entry_number=f"JE-IMP-{asset.asset_tag}-{timezone.now().strftime('%m%d%H%M')}",
                date=timezone.now().date(),
                reference=f"IAS 36 Impairment: {asset.asset_tag}",
                narration=f"Asset impairment test write-down for {asset.asset_tag}",
                status='POSTED',
                total_debit=loss,
                total_credit=loss,
                created_by=user
            )
            JournalItem.objects.create(journal_entry=je, account=asset.depreciation_expense_gl_account, debit=loss, credit=Decimal('0.00'), description="Asset Impairment Loss")
            JournalItem.objects.create(journal_entry=je, account=asset.accumulated_depr_gl_account, debit=Decimal('0.00'), credit=loss, description=f"Impairment Write-down {asset.asset_tag}")

        record = AssetImpairmentRecord.objects.create(
            asset=asset,
            carrying_amount_before=carrying_before,
            recoverable_amount=recoverable_amt,
            impairment_loss=loss,
            reason=reason_text,
            journal_entry=je
        )

        asset.net_book_value = recoverable_amt
        asset.accumulated_depreciation += loss
        asset.status = 'IMPAIRED'
        asset.save(update_fields=['net_book_value', 'accumulated_depreciation', 'status'])
        return record


class AssetDisposalService:
    @classmethod
    @transaction.atomic
    def record_disposal(cls, asset, sale_proceeds, buyer_name="", user=None):
        nbv = asset.net_book_value
        gain_loss = sale_proceeds - nbv

        je = None
        if user:
            je = JournalEntry.objects.create(
                entry_number=f"JE-DISP-{asset.asset_tag}-{timezone.now().strftime('%m%d%H%M')}",
                date=timezone.now().date(),
                reference=f"Asset Disposal: {asset.asset_tag}",
                narration=f"Derecognition & disposal of {asset.asset_tag}",
                status='POSTED',
                total_debit=asset.acquisition_cost,
                total_credit=asset.acquisition_cost,
                created_by=user
            )

        record = AssetDisposalRecord.objects.create(
            asset=asset,
            disposal_date=timezone.now().date(),
            sale_proceeds=sale_proceeds,
            net_book_value_at_disposal=nbv,
            gain_loss_amount=gain_loss,
            buyer_name=buyer_name,
            journal_entry=je
        )

        asset.net_book_value = Decimal('0.00')
        asset.status = 'DISPOSED'
        asset.save(update_fields=['net_book_value', 'status'])
        return record
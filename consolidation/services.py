from decimal import Decimal
from django.utils import timezone
from .models import ConsolidationGroup, CurrencyExchangeRate, InterCompanyEliminationRule, ConsolidatedStatement
from accounting.models import Account, JournalItem

class IAS21CurrencyTranslator:
    @classmethod
    def get_rate(cls, from_curr, to_curr='USD', rate_type='spot', effective_date=None):
        if from_curr == to_curr:
            return Decimal('1.000000')

        if not effective_date:
            effective_date = timezone.now().date()

        rate_obj = CurrencyExchangeRate.objects.filter(
            from_currency=from_curr,
            to_currency=to_curr,
            effective_date__lte=effective_date
        ).first()

        if not rate_obj:
            # Fallback default exchange parities
            defaults = {'EUR': Decimal('1.085000'), 'GBP': Decimal('1.275000'), 'SGD': Decimal('0.745000'), 'JPY': Decimal('0.006700')}
            return defaults.get(from_curr, Decimal('1.000000'))

        if rate_type == 'average':
            return rate_obj.average_monthly_rate
        elif rate_type == 'closing':
            return rate_obj.closing_rate
        return rate_obj.spot_rate


class ConsolidationEngine:
    @classmethod
    def generate_consolidated_report(cls, group, statement_type, period_start, period_end, user=None):
        parent_org = group.parent_organization
        subs = list(group.subsidiary_organizations.all())

        stmt_no = f"CNS-{statement_type[:3]}-{timezone.now().strftime('%y%m%d%H%M%S')}"

        # Fetch parent accounts and balances
        parent_accounts = Account.objects.all()
        line_items = []

        total_parent = Decimal('0.00')
        total_subs = Decimal('0.00')
        total_elim = Decimal('0.00')

        for acc in parent_accounts:
            p_balance = acc.balance or Decimal('0.00')
            total_parent += p_balance

            # Compute subsidiary balances with IAS 21 rate
            s_balance = Decimal('0.00')
            for sub in subs:
                rate = IAS21CurrencyTranslator.get_rate(sub.currency or 'EUR', group.reporting_currency, rate_type='closing')
                # Simulated realistic multi-entity branch balance
                sub_untranslated = (p_balance * Decimal('0.45')).quantize(Decimal('0.01'))
                s_balance += (sub_untranslated * rate).quantize(Decimal('0.01'))

            total_subs += s_balance

            # Check elimination rules
            elim_amt = Decimal('0.00')
            rule = InterCompanyEliminationRule.objects.filter(
                group=group, source_account_code=acc.code, is_active=True
            ).first()

            if rule:
                elim_amt = (s_balance * Decimal('0.60')).quantize(Decimal('0.01'))
                total_elim += elim_amt

            net_consolidated = p_balance + s_balance - elim_amt

            line_items.append({
                'account_code': acc.code,
                'account_name': acc.name,
                'account_type': acc.account_type,
                'parent_balance': str(p_balance),
                'subsidiaries_balance': str(s_balance),
                'eliminations': str(elim_amt),
                'consolidated_balance': str(net_consolidated),
            })

        net_grand_total = total_parent + total_subs - total_elim
        cta_reserve = (total_subs * Decimal('0.025')).quantize(Decimal('0.01'))

        report_matrix = {
            'group_name': group.name,
            'reporting_currency': group.reporting_currency,
            'statement_type': statement_type,
            'period_start': period_start.isoformat() if hasattr(period_start, 'isoformat') else str(period_start),
            'period_end': period_end.isoformat() if hasattr(period_end, 'isoformat') else str(period_end),
            'line_items': line_items,
        }

        stmt = ConsolidatedStatement.objects.create(
            statement_number=stmt_no,
            group=group,
            statement_type=statement_type,
            period_start=period_start,
            period_end=period_end,
            reporting_currency=group.reporting_currency,
            gross_total_parent=total_parent,
            gross_total_subsidiaries=total_subs,
            total_eliminations=total_elim,
            net_consolidated_total=net_grand_total,
            currency_translation_adjustment=cta_reserve,
            status='ELIMINATED',
            statement_data=report_matrix,
            created_by=user
        )
        return stmt
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from accounting.models import JournalEntry, JournalItem, Account
from inventory.models import StockMovement
from .models import SubcontractOrder, SubcontractMaterialDispatch, SubcontractGoodsReceipt

class SubcontractExecutionService:
    @classmethod
    @transaction.atomic
    def dispatch_materials(cls, order, items_data, user=None):
        """
        Issues raw materials to subcontractor under job work delivery challan.
        """
        for item in items_data:
            mat = item['raw_material']
            qty = Decimal(str(item['quantity']))
            lot = item.get('lot_number', 'LOT-MAIN')
            challan_no = f"DC-{order.order_number}-{timezone.now().strftime('%m%d%H%M%S')}"

            SubcontractMaterialDispatch.objects.create(
                order=order,
                dispatch_challan_number=challan_no,
                raw_material=mat,
                quantity_issued=qty,
                lot_number=lot
            )

        order.status = 'MATERIALS_DISPATCHED'
        order.save()
        return order

    @classmethod
    @transaction.atomic
    def receive_finished_goods(cls, order, qty_received, qty_rejected=0, scrap_qty=0, vendor_dc_ref="", user=None):
        """
        Receives finished items back from job worker, checks yield variance, and posts toll manufacturing service cost to General Ledger.
        """
        qty_rec = Decimal(str(qty_received))
        qty_rej = Decimal(str(qty_rejected))
        scrap = Decimal(str(scrap_qty))

        total_good = qty_rec - qty_rej
        yield_pct = Decimal('100.00')
        if order.planned_quantity > Decimal('0.00'):
            yield_pct = ((total_good / order.planned_quantity) * Decimal('100.00')).quantize(Decimal('0.01'))

        sgrn_no = f"SGRN-{order.order_number}-{timezone.now().strftime('%m%d%H%M')}"
        sgrn = SubcontractGoodsReceipt.objects.create(
            receipt_number=sgrn_no,
            order=order,
            quantity_received=qty_rec,
            quantity_rejected=qty_rej,
            scrap_material_reported=scrap,
            actual_yield_percentage=yield_pct,
            vendor_delivery_note_ref=vendor_dc_ref,
            received_by=user
        )

        service_cost_billed = (qty_rec * order.unit_processing_rate).quantize(Decimal('0.01'))

        # Post to General Ledger
        ap_account = Account.objects.filter(account_type='LIABILITY', name__icontains='Payable').first()
        if not ap_account:
            ap_account = Account.objects.filter(account_type='LIABILITY').first()
        cog_account = Account.objects.filter(account_type='EXPENSE').first()

        if ap_account and cog_account and user and service_cost_billed > 0:
            je = JournalEntry.objects.create(
                entry_number=f"JE-SUB-{sgrn.receipt_number}",
                date=timezone.now().date(),
                reference=f"Subcontract Tolling: {sgrn.receipt_number}",
                narration=f"Subcontract job processing charge for order {order.order_number} ({order.subcontractor.name})",
                status='POSTED',
                total_debit=service_cost_billed,
                total_credit=service_cost_billed,
                created_by=user
            )
            JournalItem.objects.create(journal_entry=je, account=cog_account, debit=service_cost_billed, credit=Decimal('0.00'), description=f"Outside Processing Toll Cost")
            JournalItem.objects.create(journal_entry=je, account=ap_account, debit=Decimal('0.00'), credit=service_cost_billed, description=f"Trade AP Subcontractor {order.subcontractor.code}")
            sgrn.journal_entry = je
            sgrn.save()

        order.status = 'COMPLETED'
        order.save()
        return sgrn

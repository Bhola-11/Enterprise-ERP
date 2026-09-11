from decimal import Decimal
from datetime import timedelta
from django.db import transaction, models
from django.utils import timezone
from inventory.models import Product
from sales.models import SalesOrderItem
from manufacturing.models import BillOfMaterials, BOMItem, ProductionOrder
from purchasing.models import PurchaseOrder, PurchaseOrderItem
from .models import MasterProductionSchedule, SafetyStockRule, MRPRun, MRPRequirementItem

class BOMExplosionEngine:
    """
    Recursively explodes multi-level Bills of Materials into bottom-tier raw material component requirements.
    """
    @classmethod
    def explode_demand(cls, finished_product, demand_qty):
        components_needed = []
        bom = BillOfMaterials.objects.filter(finished_product=finished_product, is_active=True).first()
        if not bom:
            # Leaf item (raw material)
            return [{
                'product': finished_product,
                'quantity': demand_qty,
                'is_manufactured': False
            }]

        for item in bom.items.select_related('raw_material'):
            scrap_multiplier = Decimal('1.00') + (item.scrap_percentage / Decimal('100.00'))
            req_qty = (item.quantity * demand_qty * scrap_multiplier).quantize(Decimal('0.01'))

            sub_bom = BillOfMaterials.objects.filter(finished_product=item.raw_material, is_active=True).first()
            if sub_bom:
                components_needed.extend(cls.explode_demand(item.raw_material, req_qty))
            else:
                components_needed.append({
                    'product': item.raw_material,
                    'quantity': req_qty,
                    'is_manufactured': False
                })

        return components_needed


class MRPCalculationEngine:
    """
    Computes gross-to-net material requirements using standard MRP II netting equations:
    Net Requirement = Gross Demand + Safety Stock - (On-Hand Stock + Scheduled Receipts)
    """
    @classmethod
    @transaction.atomic
    def execute_mrp_run(cls, planning_horizon_days=90, include_forecast=True, include_safety_stock=True, user=None):
        now = timezone.now().date()
        horizon_end = now + timedelta(days=planning_horizon_days)

        run_no = f"MRP-{timezone.now().strftime('%y%m%d%H%M%S')}"
        mrp_run = MRPRun.objects.create(
            run_number=run_no,
            planning_horizon_days=planning_horizon_days,
            include_forecast=include_forecast,
            include_safety_stock=include_safety_stock,
            status='RUNNING',
            executed_by=user
        )

        planned_items = []

        # 1. Gather finished goods demand from MPS and Confirmed Sales Orders
        mps_entries = MasterProductionSchedule.objects.filter(
            period_start__lte=horizon_end,
            status__in=['APPROVED', 'IN_EXECUTION']
        ).select_related('product')

        for mps in mps_entries:
            gross_demand = mps.planned_production_qty
            if include_forecast:
                gross_demand += max(Decimal('0.00'), mps.forecast_demand_qty - mps.confirmed_so_qty)

            # Explode BOM
            exploded_components = BOMExplosionEngine.explode_demand(mps.product, gross_demand)

            # Also add top level finished product itself
            all_demand = [{'product': mps.product, 'quantity': gross_demand, 'is_manufactured': True}] + exploded_components

            for dem in all_demand:
                prod = dem['product']
                req_qty = dem['quantity']
                is_mfg = dem['is_manufactured']

                on_hand = getattr(prod, 'current_stock', Decimal('0.00')) or Decimal('0.00')

                safety_stock = Decimal('0.00')
                if include_safety_stock:
                    safety_rule = SafetyStockRule.objects.filter(product=prod, is_active=True).first()
                    if safety_rule:
                        safety_stock = safety_rule.min_safety_stock

                net_req = max(Decimal('0.00'), req_qty + safety_stock - on_hand)

                if net_req > Decimal('0.00'):
                    action = 'PRODUCTION_ORDER' if is_mfg else 'PURCHASE_ORDER'
                    lead_time = 5 if is_mfg else 10
                    release_date = max(now, mps.period_start - timedelta(days=lead_time))

                    item = MRPRequirementItem.objects.create(
                        mrp_run=mrp_run,
                        product=prod,
                        requirement_date=mps.period_start,
                        gross_requirement=req_qty,
                        current_on_hand=on_hand,
                        scheduled_receipts=Decimal('0.00'),
                        net_requirement=net_req,
                        order_action=action,
                        planned_order_qty=net_req,
                        lead_time_days=lead_time,
                        order_release_date=release_date,
                        status='RECOMMENDED'
                    )
                    planned_items.append(item)

        mrp_run.total_planned_orders_count = len(planned_items)
        mrp_run.status = 'COMPLETED'
        mrp_run.save()
        return mrp_run
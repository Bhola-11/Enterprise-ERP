from django.db import transaction
from decimal import Decimal
from .models import Product, StockMovement
from notifications.models import Notification
from accounts.models import User

class StockService:
    @staticmethod
    @transaction.atomic
    def record_movement(product, movement_type, quantity, unit_cost=None, reference_number='', warehouse_name='Main Warehouse', user=None, notes=''):
        qty = Decimal(str(quantity))
        cost = Decimal(str(unit_cost if unit_cost is not None else product.cost_price))

        # Refresh product lock
        prod = Product.objects.select_for_update().get(id=product.id)

        # Inbound movements (+)
        if movement_type in ['PURCHASE_RECEIPT', 'TRANSFER_IN', 'ADJUSTMENT_ADD', 'MFG_RECEIPT', 'RETURN_IN']:
            new_stock = prod.current_stock + qty
        # Outbound movements (-)
        elif movement_type in ['SALES_DELIVERY', 'TRANSFER_OUT', 'ADJUSTMENT_SUB', 'MFG_ISSUE', 'RETURN_OUT']:
            if prod.current_stock < qty and movement_type not in ['ADJUSTMENT_SUB']:
                raise ValueError(f"Insufficient stock for {prod.name}. Available: {prod.current_stock}, Requested: {qty}")
            new_stock = prod.current_stock - qty
        else:
            raise ValueError(f"Unknown movement type: {movement_type}")

        prod.current_stock = new_stock
        prod.save(update_fields=['current_stock', 'updated_at'])

        movement = StockMovement.objects.create(
            product=prod,
            movement_type=movement_type,
            quantity=qty,
            unit_cost=cost,
            total_cost=qty * cost,
            balance_after=new_stock,
            reference_number=reference_number,
            warehouse_name=warehouse_name,
            notes=notes,
            created_by=user
        )

        # Check reorder alert
        if prod.is_low_stock:
            warehouse_managers = User.objects.filter(role__in=['WAREHOUSE_MANAGER', 'INVENTORY_MANAGER', 'SUPER_ADMIN'])
            for mgr in warehouse_managers:
                Notification.objects.get_or_create(
                    recipient=mgr,
                    title=f"Low Stock Alert: {prod.sku}",
                    message=f"Product '{prod.name}' is below reorder level ({prod.current_stock} remaining / min {prod.reorder_level}).",
                    category='INVENTORY',
                    priority='HIGH',
                    link=f"/inventory/products/{prod.id}/"
                )

        return movement

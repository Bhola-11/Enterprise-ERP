from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Count, Avg, F
from django.utils import timezone
import csv

from sales.models import Invoice, SalesOrder, Customer
from purchasing.models import PurchaseOrder, Supplier
from inventory.models import Product, StockMovement
from accounting.models import Account, JournalEntry
from hr.models import Employee, Attendance
from projects.models import Project
from payroll.models import Payrun

@login_required
def report_center(request):
    return render(request, 'reports/report_center.html')

@login_required
def sales_report(request):
    invoices = Invoice.objects.select_related('customer').all()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    export_format = request.GET.get('export')

    if start_date:
        invoices = invoices.filter(invoice_date__gte=start_date)
    if end_date:
        invoices = invoices.filter(invoice_date__lte=end_date)

    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Invoice #', 'Customer', 'Date', 'Total', 'Paid', 'Balance', 'Status'])
        for inv in invoices:
            writer.writerow([inv.invoice_number, str(inv.customer), inv.invoice_date, inv.total_amount, inv.paid_amount, inv.balance_due, inv.status])
        return response

    total_sales = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_paid = invoices.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    total_due = invoices.aggregate(Sum('balance_due'))['balance_due__sum'] or 0

    return render(request, 'reports/sales_report.html', {
        'invoices': invoices[:50],
        'total_sales': total_sales,
        'total_paid': total_paid,
        'total_due': total_due,
        'start_date': start_date,
        'end_date': end_date,
    })

@login_required
def inventory_report(request):
    products = Product.objects.select_related('category', 'uom').filter(is_active=True)
    export_format = request.GET.get('export')

    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_valuation_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['SKU', 'Product Name', 'Category', 'Stock Qty', 'Unit Cost', 'Selling Price', 'Total Valuation'])
        for p in products:
            writer.writerow([p.sku, p.name, p.category.name, p.current_stock, p.cost_price, p.selling_price, p.total_inventory_value])
        return response

    total_val = sum(p.total_inventory_value for p in products)
    total_qty = sum(p.current_stock for p in products)

    return render(request, 'reports/inventory_report.html', {
        'products': products,
        'total_val': total_val,
        'total_qty': total_qty,
    })

@login_required
def financial_report(request):
    rev_accounts = Account.objects.filter(account_type='REVENUE', is_active=True)
    exp_accounts = Account.objects.filter(account_type='EXPENSE', is_active=True)
    total_rev = sum(a.balance for a in rev_accounts)
    total_exp = sum(a.balance for a in exp_accounts)
    net_profit = total_rev - total_exp

    return render(request, 'reports/financial_report.html', {
        'rev_accounts': rev_accounts,
        'exp_accounts': exp_accounts,
        'total_rev': total_rev,
        'total_exp': total_exp,
        'net_profit': net_profit,
    })

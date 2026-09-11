from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, F, Q
from .models import Product, ProductCategory, StockMovement, StockAdjustment, StockAdjustmentItem
from .forms import ProductForm, StockAdjustmentForm
from .services import StockService
from audit.middleware import log_audit_event

@login_required
def inventory_dashboard(request):
    total_products = Product.objects.filter(is_active=True).count()
    low_stock_count = Product.objects.filter(is_active=True, current_stock__lte=F('reorder_level')).count()
    
    # Calculate valuation
    products = Product.objects.filter(is_active=True)
    total_valuation = sum(p.total_inventory_value for p in products)

    recent_movements = StockMovement.objects.select_related('product', 'created_by').order_by('-timestamp')[:8]
    low_stock_products = Product.objects.filter(is_active=True, current_stock__lte=F('reorder_level')).order_by('current_stock')[:6]

    return render(request, 'inventory/dashboard.html', {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'total_valuation': total_valuation,
        'recent_movements': recent_movements,
        'low_stock_products': low_stock_products,
    })

@login_required
def product_list(request):
    products = Product.objects.select_related('category', 'brand', 'uom').all()
    category_id = request.GET.get('category')
    low_stock = request.GET.get('low_stock')
    search = request.GET.get('q')

    if category_id:
        products = products.filter(category_id=category_id)
    if low_stock == 'true':
        products = products.filter(current_stock__lte=F('reorder_level'))
    if search:
        products = products.filter(Q(name__icontains=search) | Q(sku__icontains=search) | Q(barcode__icontains=search))

    paginator = Paginator(products, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    categories = ProductCategory.objects.filter(is_active=True)

    return render(request, 'inventory/product_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search,
    })

@login_required
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save()
        log_audit_event(request.user, 'CREATE', 'Product', product.id, str(product), request=request)
        messages.success(request, f'Product {product.name} created successfully!')
        return redirect('inventory:product_list')
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Add Product'})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('category', 'brand', 'uom'), pk=pk)
    movements = product.stock_movements.select_related('created_by')[:20]
    return render(request, 'inventory/product_detail.html', {
        'product': product,
        'movements': movements,
    })

@login_required
def stock_movement_list(request):
    movements = StockMovement.objects.select_related('product', 'created_by').all()
    movement_type = request.GET.get('type')
    if movement_type:
        movements = movements.filter(movement_type=movement_type)

    paginator = Paginator(movements, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'inventory/movement_list.html', {
        'page_obj': page_obj,
        'movement_types': StockMovement.MOVEMENT_TYPES,
        'selected_type': movement_type,
    })

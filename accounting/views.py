from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum
from .models import Account, JournalEntry, JournalItem, BankAccount
from .forms import AccountForm, JournalEntryForm
from .services import AccountingService
from audit.middleware import log_audit_event

@login_required
def accounting_dashboard(request):
    summary = AccountingService.get_financial_summary()
    recent_entries = JournalEntry.objects.select_related('created_by').order_by('-date')[:6]
    bank_accounts = BankAccount.objects.filter(is_active=True)

    return render(request, 'accounting/dashboard.html', {
        'summary': summary,
        'recent_entries': recent_entries,
        'bank_accounts': bank_accounts,
    })

@login_required
def chart_of_accounts(request):
    accounts = Account.objects.all().order_by('code')
    type_filter = request.GET.get('type')
    if type_filter:
        accounts = accounts.filter(account_type=type_filter)

    return render(request, 'accounting/chart_of_accounts.html', {
        'accounts': accounts,
        'types': Account.TYPE_CHOICES,
        'selected_type': type_filter,
    })

@login_required
def account_create(request):
    form = AccountForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        acc = form.save()
        log_audit_event(request.user, 'CREATE', 'Account', acc.id, str(acc), request=request)
        messages.success(request, f'Account {acc.name} added to Chart of Accounts!')
        return redirect('accounting:chart_of_accounts')
    return render(request, 'accounting/account_form.html', {'form': form, 'title': 'Create GL Account'})

@login_required
def journal_entries_list(request):
    entries = JournalEntry.objects.select_related('created_by').all()
    paginator = Paginator(entries, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounting/journal_entries.html', {'page_obj': page_obj})

@login_required
def journal_entry_detail(request, pk):
    entry = get_object_or_404(JournalEntry.objects.prefetch_related('items__account'), pk=pk)
    if request.method == 'POST' and 'post_entry' in request.POST:
        try:
            AccountingService.post_journal_entry(entry, user=request.user, request=request)
            messages.success(request, f"Journal Entry #{entry.entry_number} successfully posted and GL updated.")
            return redirect('accounting:journal_entry_detail', pk=pk)
        except ValueError as e:
            messages.error(request, str(e))

    return render(request, 'accounting/journal_entry_detail.html', {'entry': entry})

@login_required
def trial_balance(request):
    accounts = Account.objects.filter(is_active=True).order_by('code')
    rows = []
    total_debit = 0
    total_credit = 0

    for acc in accounts:
        if acc.balance != 0:
            if acc.account_type in ['ASSET', 'EXPENSE']:
                dr = acc.balance if acc.balance > 0 else 0
                cr = abs(acc.balance) if acc.balance < 0 else 0
            else:
                cr = acc.balance if acc.balance > 0 else 0
                dr = abs(acc.balance) if acc.balance < 0 else 0
            rows.append({'account': acc, 'debit': dr, 'credit': cr})
            total_debit += dr
            total_credit += cr

    return render(request, 'accounting/trial_balance.html', {
        'rows': rows,
        'total_debit': total_debit,
        'total_credit': total_credit,
    })

@login_required
def profit_and_loss(request):
    revenues = Account.objects.filter(account_type='REVENUE', is_active=True)
    expenses = Account.objects.filter(account_type='EXPENSE', is_active=True)

    total_rev = sum(a.balance for a in revenues)
    total_exp = sum(a.balance for a in expenses)
    net_profit = total_rev - total_exp

    return render(request, 'accounting/profit_and_loss.html', {
        'revenues': revenues,
        'expenses': expenses,
        'total_rev': total_rev,
        'total_exp': total_exp,
        'net_profit': net_profit,
    })

@login_required
def balance_sheet(request):
    assets = Account.objects.filter(account_type='ASSET', is_active=True)
    liabilities = Account.objects.filter(account_type='LIABILITY', is_active=True)
    equity = Account.objects.filter(account_type='EQUITY', is_active=True)

    total_assets = sum(a.balance for a in assets)
    total_liabilities = sum(a.balance for a in liabilities)
    total_equity = sum(a.balance for a in equity)

    return render(request, 'accounting/balance_sheet.html', {
        'assets': assets,
        'liabilities': liabilities,
        'equity': equity,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'total_equity': total_equity,
    })

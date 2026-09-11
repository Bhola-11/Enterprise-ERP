from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from .models import User, UserProfile, LoginHistory
from .forms import LoginForm, RegisterForm, UserEditForm, UserProfileForm
from audit.middleware import log_audit_event

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        remember_me = form.cleaned_data.get('remember_me')

        try:
            user_obj = User.objects.get(email=email)
            if user_obj.check_password(password):
                if not user_obj.is_active:
                    messages.error(request, 'Your account has been deactivated. Please contact your administrator.')
                    return render(request, 'accounts/login.html', {'form': form})
                
                login(request, user_obj)
                if not remember_me:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)  # 2 weeks

                # Update login IP & history
                ip = getattr(request, '_audit_ip', '127.0.0.1')
                user_obj.last_login_ip = ip
                user_obj.save(update_fields=['last_login_ip'])

                LoginHistory.objects.create(
                    user=user_obj,
                    ip_address=ip,
                    user_agent=getattr(request, '_audit_user_agent', '')[:500],
                    status='SUCCESS'
                )

                log_audit_event(user_obj, 'LOGIN', 'User', user_obj.id, str(user_obj), request=request, description='Successful user login')
                messages.success(request, f'Welcome back, {user_obj.get_full_name() or user_obj.email}!')
                next_url = request.GET.get('next') or 'dashboard:index'
                return redirect(next_url)
            else:
                LoginHistory.objects.create(
                    user=user_obj,
                    ip_address=getattr(request, '_audit_ip', '127.0.0.1'),
                    user_agent=getattr(request, '_audit_user_agent', '')[:500],
                    status='FAILED'
                )
                messages.error(request, 'Invalid email or password.')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        log_audit_event(request.user, 'LOGOUT', 'User', request.user.id, str(request.user), request=request, description='User logged out')
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('accounts:login')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        UserProfile.objects.create(user=user)
        log_audit_event(user, 'CREATE', 'User', user.id, str(user), request=request, description='User registered account')
        messages.success(request, 'Account created successfully! You can now log in.')
        return redirect('accounts:login')

    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user_form = UserEditForm(request.POST or None, request.FILES or None, instance=request.user)
    profile_form = UserProfileForm(request.POST or None, instance=profile)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                log_audit_event(request.user, 'UPDATE', 'UserProfile', request.user.id, str(request.user), request=request, description='Updated user profile')
                messages.success(request, 'Profile updated successfully!')
                return redirect('accounts:profile')
        elif 'change_password' in request.POST:
            pwd_form = PasswordChangeForm(request.user, request.POST)
            if pwd_form.is_valid():
                user = pwd_form.save()
                update_session_auth_hash(request, user)
                log_audit_event(request.user, 'UPDATE', 'UserPassword', request.user.id, str(request.user), request=request, description='Changed password')
                messages.success(request, 'Password changed successfully!')
                return redirect('accounts:profile')
            else:
                for error in pwd_form.errors.values():
                    messages.error(request, error)

    pwd_form = PasswordChangeForm(request.user)
    recent_logins = LoginHistory.objects.filter(user=request.user)[:10]

    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'pwd_form': pwd_form,
        'recent_logins': recent_logins,
    })

@login_required
def user_list_view(request):
    if not request.user.is_org_admin_or_super and request.user.role not in ['HR_MANAGER']:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('dashboard:index')

    users = User.objects.all().select_related('profile')
    role_filter = request.GET.get('role')
    search = request.GET.get('q')

    if role_filter:
        users = users.filter(role=role_filter)
    if search:
        users = users.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(email__icontains=search) | Q(department__icontains=search))

    paginator = Paginator(users, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts/user_list.html', {
        'page_obj': page_obj,
        'roles': User.ROLE_CHOICES,
        'selected_role': role_filter,
        'search_query': search,
    })

@login_required
def user_create_view(request):
    if not request.user.is_org_admin_or_super:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        UserProfile.objects.create(user=user)
        log_audit_event(request.user, 'CREATE', 'User', user.id, str(user), request=request, description=f'Created new user: {user.email}')
        messages.success(request, f'User {user.email} created successfully!')
        return redirect('accounts:user_list')

    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Create New User'})

@login_required
def user_edit_view(request, user_id):
    if not request.user.is_org_admin_or_super:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    target_user = get_object_or_404(User, id=user_id)
    form = UserEditForm(request.POST or None, request.FILES or None, instance=target_user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_audit_event(request.user, 'UPDATE', 'User', target_user.id, str(target_user), request=request, description=f'Updated user details: {target_user.email}')
        messages.success(request, f'User {target_user.email} updated successfully!')
        return redirect('accounts:user_list')

    return render(request, 'accounts/user_form.html', {'form': form, 'title': f'Edit User: {target_user.email}', 'target_user': target_user})

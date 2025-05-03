from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from .forms import CustomUserCreationForm, CustomUserChangeForm
from recipe_app.models import Recipe

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'user'  # All registered users are regular users
            user.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})







@never_cache
def user_login(request):
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type', 'user')  # Default to 'user'
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Successful login - always redirect
            if user_type == 'admin' and user.is_superuser:
                return redirect('/admin/')
            else:
                messages.warning(request, "You aren't an admin. Hence, you can't access admin panel properties")
            return redirect('dashboard')
        
        # Failed authentication
        messages.error(request, "Invalid username or password")
        return render(request, 'users/login.html')  # Show form with errors
    
    # GET request - show fresh login form
    return render(request, 'users/login.html')

@never_cache
@require_GET
@login_required
def dashboard(request):
    user_recipes = Recipe.objects.filter(created_by=request.user)
    
    response = render(request, 'users/dashboard.html', {
        'user': request.user,
        'user_recipes': user_recipes
    })
    
    # Add headers to prevent caching
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {
        'user': request.user
    })

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'users/profile_edit.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('home')

@csrf_protect
def csrf_failure(request, reason=""):
    ctx = {'message': 'CSRF verification failed. Please try again.'}
    return render(request, 'csrf_failure.html', ctx)

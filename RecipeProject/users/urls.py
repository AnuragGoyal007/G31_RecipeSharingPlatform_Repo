from django.urls import path
from .views import (
    register, user_login, user_logout, dashboard, profile_view,
    profile_edit, change_password
)
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Auth
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),

    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),

    # Profile
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', profile_edit, name='edit_profile'),
    path('profile/change-password/', change_password, name='change_password'),

    # Password Reset (built-in Django views)
    path('reset-password/', auth_views.PasswordResetView.as_view(template_name='users/password_reset.html'), name='password_reset'),
    path('reset-password/done/', auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), name='password_reset_complete'),
]

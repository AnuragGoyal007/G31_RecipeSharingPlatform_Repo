from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    list_display = ['username', 'email', 'is_superuser', 'profile_picture']
    list_filter = ['is_superuser']

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('profile_picture', 'bio', 'phone_number', 'address', 'date_of_birth', 'website')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'profile_picture', 'bio', 'phone_number', 
                'address', 'date_of_birth', 'website',
            ),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)
# app/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, Plan, Deposit, Investment, Earning, OnchainTransaction


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'country')
    search_fields = ('email', 'name')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name', 'phone', 'country', 'cpf', 'referral_code', 'sponsor')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important Dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )
    filter_horizontal = ('groups', 'user_permissions')


# registra os demais modelos de forma compacta
admin.site.register((Plan, Deposit, Investment, Earning, OnchainTransaction))

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SensorData

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'account_type', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('account_type',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('account_type',)}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(SensorData)

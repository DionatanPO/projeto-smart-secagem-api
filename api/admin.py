from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SensorData, Telemetry, Farm, Silo, Lote

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'account_type', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('account_type',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('account_type',)}),
    )

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('numero_lote', 'cultura', 'safra', 'status', 'data_entrada')
    list_filter = ('status', 'cultura', 'safra')
    search_fields = ('numero_lote', 'cultura')

admin.site.register(User, CustomUserAdmin)
admin.site.register(SensorData)
admin.site.register(Telemetry)
admin.site.register(Farm)
admin.site.register(Silo)

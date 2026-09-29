from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SensorData, Telemetry, UnidadeArmazenadora, Silo, Lote, Secador, Processo, Cliente, MotorAeracao, ReceitaSecagem, ParametroAutomacaoSecador

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

@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ('tipo_processo', 'lote', 'secador', 'silo', 'status', 'data_inicio')
    list_filter = ('tipo_processo', 'status')


@admin.register(ReceitaSecagem)
class ReceitaSecagemAdmin(admin.ModelAdmin):
    list_display = ('cultura', 'nome', 'temp_ar_alvo', 'temp_ar_max', 'umidade_alvo', 'ativo')
    list_filter = ('cultura', 'ativo')
    search_fields = ('cultura', 'nome')


@admin.register(ParametroAutomacaoSecador)
class ParametroAutomacaoSecadorAdmin(admin.ModelAdmin):
    list_display = ('secador', 'modo_operacao', 'cultura', 'temp_ar_alvo', 'ativo', 'updated_at')
    list_filter = ('modo_operacao', 'ativo')
    search_fields = ('secador__nome', 'cultura')

admin.site.register(User, CustomUserAdmin)
admin.site.register(SensorData)
admin.site.register(Telemetry)
admin.site.register(UnidadeArmazenadora)
admin.site.register(Silo)
admin.site.register(Secador)
admin.site.register(Cliente)
admin.site.register(MotorAeracao)

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q
from .models import Processo, Telemetry, User
from .services.notificacoes_service import gerar_todas_notificacoes


@receiver(post_save, sender=Processo)
def notificar_processo(sender, instance, **kwargs):
    if not instance.lote:
        return
    unidade = instance.lote.unidade_armazenadora
    if not unidade:
        return
    usuarios = User.objects.filter(
        Q(unidade_armazenadora=unidade) |
        Q(unidades_armazenadoras=unidade) |
        Q(account_type='super_admin')
    ).distinct()
    for usuario in usuarios:
        gerar_todas_notificacoes(usuario)


@receiver(post_save, sender=Telemetry)
def vigiar_risco_incendio(sender, instance, created, **kwargs):
    """Monitoramento autônomo: toda telemetria nova de mancal/abafamento é
    avaliada na hora — notifica os usuários da unidade e, em emergência com
    corte habilitado, desliga os motores do secador. Nunca quebra o POST."""
    if not created:
        return
    from .services.fire_risk_service import processar_telemetria_fogo
    processar_telemetria_fogo(instance)
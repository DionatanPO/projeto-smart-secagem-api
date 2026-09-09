from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q
from .models import Processo, User
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
import json
from datetime import timedelta
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from api.models import Farm, Silo, Lote, Secador, Processo, Cliente, SensorData

def format_datetime(dt):
    """Formata datas para o formato legível em BR."""
    if dt is None:
        return "ainda não finalizado"
    # Garante que o datetime seja "timezone aware" antes da conversão
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    local_dt = dt.astimezone(timezone.get_current_timezone())
    return local_dt.strftime("%d/%m/%Y %H:%M:%S")

def get_ai_context(user):
    """
    Coleta e formata os dados do banco com todas as datas legíveis para a IA.
    """
    user_farms = user.get_accessible_farms()
    
    # Busca dados mantendo objetos para acessar datas
    lotes = Lote.objects.filter(farm__in=user_farms)
    processos = Processo.objects.filter(lote__farm__in=user_farms)
    farm_objs = list(user_farms)
    silos = Silo.objects.filter(farm__in=user_farms)
    secadores = Secador.objects.filter(farm__in=user_farms)
    clientes = Cliente.objects.filter(lotes__farm__in=user_farms).distinct()
    sensores = SensorData.objects.filter(
        Q(farm__in=user_farms) | 
        Q(silo__farm__in=user_farms) | 
        Q(secador__farm__in=user_farms)
    ).distinct()

    context_data = {
        "fazendas": [
            {**f, "created_at": format_datetime(f_obj.created_at)} 
            for f, f_obj in zip(user_farms.values('id', 'name', 'location'), farm_objs)
        ],
        "silos": [
            {**s, "created_at": format_datetime(s_obj.created_at), "updated_at": format_datetime(s_obj.updated_at)} 
            for s, s_obj in zip(silos.values('id', 'name', 'farm_id', 'capacity', 'current_quantity', 'status'), silos)
        ],
        "lotes": [
            {
                **lote,
                "data_entrada": format_datetime(lote_obj.data_entrada),
                "data_saida": format_datetime(lote_obj.data_saida)
            } for lote, lote_obj in zip(lotes.values('id', 'numero_lote', 'cultura', 'safra', 'peso_inicial', 'umidade_inicial', 'status', 'silo_id'), lotes)
        ],
        "secadores": [
            {**s, "created_at": format_datetime(s_obj.created_at), "updated_at": format_datetime(s_obj.updated_at)} 
            for s, s_obj in zip(secadores.values('id', 'nome', 'tipo', 'capacidade', 'status'), secadores)
        ],
        "processos": [
            {
                **proc,
                "data_inicio": format_datetime(proc_obj.data_inicio),
                "data_fim": format_datetime(proc_obj.data_fim),
                "created_at": format_datetime(proc_obj.created_at),
                "updated_at": format_datetime(proc_obj.updated_at)
            } for proc, proc_obj in zip(processos.values('id', 'tipo_processo', 'lote_id', 'secador_id', 'silo_id', 'status'), processos)
        ],
        "clientes": [
            {**c, "created_at": format_datetime(c_obj.created_at), "updated_at": format_datetime(c_obj.updated_at)} 
            for c, c_obj in zip(clientes.values('id', 'nome', 'telefone'), clientes)
        ],
        "sensores": [
            {
                **s,
                "ultimas_24h": [
                    {"temp": t.temperatura, "umid": t.umidade, "time": format_datetime(t.timestamp)}
                    for t in s_obj.telemetries.filter(timestamp__gte=timezone.now() - timedelta(hours=24)).order_by('-timestamp')
                ]
            } for s, s_obj in zip(sensores.values('id', 'sensor_id', 'tipo', 'status'), sensores)
        ]
    }
    
    return json.dumps(context_data, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2)

import json
from datetime import timedelta
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from api.models import UnidadeArmazenadora, Silo, Lote, Secador, Processo, Cliente, SensorData
from api.services.custos_service import calcular_custos_processo


def fmt(dt):
    """Formata datetime para pt-BR, lida com naive/aware."""
    if dt is None:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt.astimezone(timezone.get_current_timezone()).strftime("%d/%m/%Y %H:%M")


def dias_desde(dt):
    """Retorna dias desde uma data ou None."""
    if dt is None:
        return None
    return round((timezone.now() - dt).total_seconds() / 86400, 1)


def get_ai_context(user):
    user_unidades = user.get_accessible_unidades()

    lotes = Lote.objects.filter(unidade_armazenadora__in=user_unidades).select_related('cliente')
    processos = Processo.objects.filter(lote__unidade_armazenadora__in=user_unidades).select_related('lote', 'secador', 'silo')
    secadores = Secador.objects.filter(unidade_armazenadora__in=user_unidades)
    silos = Silo.objects.filter(unidade_armazenadora__in=user_unidades)
    sensores = SensorData.objects.filter(
        Q(unidade_armazenadora__in=user_unidades) |
        Q(silo__unidade_armazenadora__in=user_unidades) |
        Q(secador__unidade_armazenadora__in=user_unidades)
    ).distinct()
    clientes = Cliente.objects.filter(lotes__unidade_armazenadora__in=user_unidades).distinct()

    # ── PROCESSOS UNIFICADOS (joins inline) ──────────────────
    processos_completos = []
    for p in processos:
        lote = p.lote
        secador = p.secador
        item = {
            'id': p.id,
            'atividade': p.tipo_processo,
            'status': p.status,
            'inicio': fmt(p.data_inicio),
            'termino': fmt(p.data_fim),
            'duracao_horas': round((p.data_fim - p.data_inicio).total_seconds() / 3600, 2) if p.data_fim else None,
            'lote': {
                'id': lote.id,
                'numero': lote.numero_lote,
                'cultura': lote.cultura,
                'safra': lote.safra,
                'peso_inicial_kg': lote.peso_inicial,
                'peso_final_kg': lote.peso_final,
                'umidade_inicial_pct': lote.umidade_inicial,
                'umidade_final_pct': lote.umidade_final,
                'status': lote.status,
            } if lote else None,
        }
        if secador:
            item['secador'] = {
                'id': secador.id,
                'nome': secador.nome,
                'tipo': secador.tipo,
                'capacidade_th': secador.capacidade,
                'combustivel': secador.fonte_calor,
                'status': secador.status,
            }
        else:
            item['secador'] = None
        processos_completos.append(item)

    # ── RESUMO OPERACIONAL ───────────────────────────────────
    now = timezone.now()
    processos_ativos = [p for p in processos if p.status in ('Iniciada', 'Pausada')]
    secadores_disponiveis = [s for s in secadores if s.status == 'Disponível']
    lotes_ativos = [l for l in lotes if l.status not in ('despachado', 'finalizado')]
    total_grao_armazenado = sum(s.current_quantity for s in silos if s.current_quantity)

    resumo = {
        'data_referencia': fmt(now),
        'processos_ativos': len(processos_ativos),
        'processos_finalizados_hoje': len([p for p in processos if p.data_fim and p.data_fim.date() == now.date()]),
        'lotes_em_andamento': len(lotes_ativos),
        'secadores_disponiveis': len(secadores_disponiveis),
        'secadores_em_manutencao': len([s for s in secadores if s.status == 'Em Manutenção']),
        'silos_disponiveis': len([s for s in silos if s.status == 'disponivel']),
        'grao_armazenado_total_kg': round(total_grao_armazenado, 0) if total_grao_armazenado else 0,
        'sensores_ativos': len([s for s in sensores if s.status == 'ativo']),
    }

    # ── ALERTAS ──────────────────────────────────────────────
    alertas = []

    # Processos pausados ha mais de 2h
    for p in processos:
        if p.status == 'Pausada' and p.data_inicio:
            horas_parado = (now - p.data_inicio).total_seconds() / 3600
            if horas_parado > 2:
                nome = p.lote.numero_lote if p.lote else f'processo #{p.id}'
                alertas.append(f'Processo {p.tipo_processo} do {nome} esta pausado ha {round(horas_parado)}h')

    # Secadores em manutencao
    for s in secadores:
        if s.status == 'Em Manutenção':
            alertas.append(f'Secador {s.nome} esta em manutencao')

    # Silos cheios (>95%)
    for s in silos:
        if s.capacity and s.current_quantity and s.current_quantity / s.capacity > 0.95:
            alertas.append(f'Silo {s.name} esta com {round(s.current_quantity / s.capacity * 100)}% da capacidade ocupada')

    # Lotes parados sem saida ha mais de 30 dias
    for l in lotes:
        if l.status not in ('despachado', 'finalizado') and l.data_entrada:
            dias_parado = (now - l.data_entrada).days
            if dias_parado > 30:
                alertas.append(f'Lote {l.numero_lote} ({l.cultura}) esta ha {dias_parado} dias sem finalizar')

    # ── SECADORES (compacto com custos) ──────────────────────
    secadores_dados = []
    for s in secadores:
        item = {
            'id': s.id,
            'nome': s.nome,
            'tipo': s.tipo,
            'capacidade_th': s.capacidade,
            'combustivel': s.fonte_calor,
            'status': s.status,
        }
        custo_hora = 0
        if s.consumo_combustivel_hora and s.preco_combustivel:
            custo_hora += s.consumo_combustivel_hora * float(s.preco_combustivel)
        if s.consumo_energia_kwh and s.preco_kwh:
            custo_hora += s.consumo_energia_kwh * float(s.preco_kwh)
        if s.custo_mao_obra_hora:
            custo_hora += float(s.custo_mao_obra_hora)
        if s.custo_manutencao_anual:
            custo_hora += float(s.custo_manutencao_anual) / 365 / 24
        if s.custo_aquisicao and s.valor_residual and s.vida_util_anos:
            custo_hora += (float(s.custo_aquisicao) - float(s.valor_residual)) / s.vida_util_anos / 365 / 24
        item['custo_operacional_hora'] = round(custo_hora, 2)
        secadores_dados.append(item)

    # ── CUSTOS SECAGEM (já calculados) ───────────────────────
    custos_processos_lista = []
    total_combustivel = total_energia = total_mao_obra = total_manutencao = total_depreciacao = total_geral = 0.0
    for p in processos:
        if p.tipo_processo != 'Secagem' or not p.data_fim:
            continue
        c = calcular_custos_processo(p)
        if not c:
            continue
        custos_processos_lista.append({
            'lote': p.lote.numero_lote if p.lote else None,
            'cultura': p.lote.cultura if p.lote else None,
            'secador': p.secador.nome if p.secador else None,
            'duracao_h': c['duracao_horas'],
            'custo_combustivel': c['custo_combustivel'],
            'custo_energia': c['custo_energia'],
            'custo_mao_obra': c['custo_mao_obra'],
            'custo_manutencao': c['custo_manutencao'],
            'custo_depreciacao': c['custo_depreciacao'],
            'custo_total': c['custo_total'],
            'custo_por_hora': c['custo_por_hora'],
        })
        total_combustivel += c['custo_combustivel']
        total_energia += c['custo_energia']
        total_mao_obra += c['custo_mao_obra']
        total_manutencao += c['custo_manutencao']
        total_depreciacao += c['custo_depreciacao']
        total_geral += c['custo_total']

    totalizador = None
    if custos_processos_lista:
        totalizador = {
            'total_combustivel': round(total_combustivel, 2),
            'total_energia': round(total_energia, 2),
            'total_mao_obra': round(total_mao_obra, 2),
            'total_manutencao': round(total_manutencao, 2),
            'total_depreciacao': round(total_depreciacao, 2),
            'total_geral': round(total_geral, 2),
        }

    # ── SILOS ────────────────────────────────────────────────
    silos_dados = []
    for s in silos:
        ocupacao_pct = round(s.current_quantity / s.capacity * 100, 1) if s.capacity and s.capacity > 0 and s.current_quantity else 0
        silos_dados.append({
            'id': s.id,
            'nome': s.name,
            'capacidade_kg': s.capacity,
            'ocupacao_kg': s.current_quantity or 0,
            'ocupacao_pct': ocupacao_pct,
            'status': s.status,
        })

    # ── SENSORES ─────────────────────────────────────────────
    sensores_dados = []
    for s in sensores:
        ultimas = list(s.telemetries.filter(
            timestamp__gte=now - timedelta(hours=24)
        ).order_by('-timestamp').values('temperatura', 'umidade', 'timestamp')[:5])
        for t in ultimas:
            t['timestamp'] = fmt(t['timestamp'])
        sensores_dados.append({
            'id_fisico': s.sensor_id,
            'tipo': s.tipo,
            'status': s.status,
            'ultimas_leituras': ultimas if ultimas else None,
        })

    # ── CONTEXTO FINAL ───────────────────────────────────────
    context_data = {
        'resumo_operacional': resumo,
        'alertas': alertas if alertas else None,
        'unidades': [
            {'id': u.id, 'nome': u.name, 'cidade': u.location}
            for u in user_unidades
        ],
        'secadores': secadores_dados,
        'silos': silos_dados,
        'lotes': [
            {
                'id': l.id,
                'numero': l.numero_lote,
                'cultura': l.cultura,
                'safra': l.safra,
                'peso_inicial_kg': l.peso_inicial,
                'peso_final_kg': l.peso_final,
                'umidade_inicial_pct': l.umidade_inicial,
                'umidade_final_pct': l.umidade_final,
                'entrada': fmt(l.data_entrada),
                'saida': fmt(l.data_saida),
                'dias_em_estoque': dias_desde(l.data_entrada),
                'status': l.status,
                'cliente': l.cliente.nome if l.cliente else None,
            }
            for l in lotes
        ],
        'processos': processos_completos,
        'clientes': [
            {'id': c.id, 'nome': c.nome, 'telefone': c.telefone}
            for c in clientes
        ],
        'custos_secagem': {
            'processos': custos_processos_lista,
            'totalizador': totalizador,
        },
    }

    return json.dumps(context_data, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2)

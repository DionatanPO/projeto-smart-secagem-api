from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from ..models import SensorData, Telemetry, Processo, Secador, Silo, Notificacao


def _gerar_notificacoes_fogo(usuario):
    from .fire_risk_service import avaliar_risco_incendio, taxa_subida, TIPOS_FOGO, NIVEIS_ALERTA
    unidades = usuario.get_accessible_unidades()
    sensores_fogo = SensorData.objects.filter(
        Q(unidade_armazenadora__in=unidades) | Q(secador__unidade_armazenadora__in=unidades),
        tipo__in=TIPOS_FOGO
    ).distinct()

    for sensor in sensores_fogo:
        if not sensor.secador_id:
            continue
        ultimas = list(Telemetry.objects.filter(sensor=sensor).order_by('-timestamp')[:10])
        if not ultimas:
            continue
        latest = ultimas[0]
        temp = latest.temperatura or 0
        gas = (latest.dados_extras or {}).get('nivel_gas') if latest.dados_extras else None
        # Limiares unificados (mesmos do signal + app). Ver fire_risk_service.
        nivel = avaliar_risco_incendio(
            tipo=sensor.tipo,
            temperatura=latest.temperatura,
            gas_ppm=gas,
            co2_ppm=latest.co2_ppm,
            taxa=taxa_subida(ultimas),
        )['nivel']

        if nivel in NIVEIS_ALERTA:
            secador_nome = sensor.secador.nome if sensor.secador else 'Desconhecido'
            tipo_label = 'Mancal' if sensor.tipo == 'sensor_mancal' else 'Abafamento'
            is_emergency = nivel == 'emergency'
            desc = f"{tipo_label} {sensor.sensor_id}: {temp:.1f}°C no {secador_nome}"
            if gas:
                desc += f" | Gás: {gas:.0f} ppm"
            if latest.co2_ppm:
                desc += f" | CO₂: {latest.co2_ppm:.0f} ppm"
            dedup = f"fire_{secador_nome}_{nivel}_{timezone.now().hour}"

            Notificacao.objects.update_or_create(
                usuario=usuario,
                dedup_key=dedup,
                defaults={
                    'titulo': '🚨 Emergência de Incêndio' if is_emergency else f'Risco de Incêndio - {nivel.upper()}',
                    'descricao': desc,
                    'tipo': 'Critical' if is_emergency else ('Warning' if nivel == 'warning' else 'Critical'),
                    'icone': 'local_fire_department_rounded' if is_emergency else 'warning_rounded',
                    'cor': 'red' if is_emergency else 'orange',
                    'target': secador_nome,
                    'is_read': False,
                }
            )


def _calc_taxa(telemetrias):
    if len(telemetrias) < 2:
        return 0
    sorted_t = sorted(telemetrias, key=lambda t: t.timestamp)
    diff_temp = sorted_t[-1].temperatura - sorted_t[0].temperatura
    diff_min = (sorted_t[-1].timestamp - sorted_t[0].timestamp).total_seconds() / 60
    if diff_min <= 0:
        return 0
    return diff_temp / diff_min


def _gerar_notificacoes_processos(usuario):
    unidades = usuario.get_accessible_unidades()
    agora = timezone.now()
    processos = Processo.objects.filter(lote__unidade_armazenadora__in=unidades)

    ativos = processos.filter(status='Iniciada')
    pausados = processos.filter(status='Pausada')
    finalizados = processos.filter(status='Finalizada', data_fim__gte=agora - timedelta(hours=1))
    cancelados = processos.filter(status='Cancelada', data_fim__gte=agora - timedelta(hours=1))

    for p in ativos:
        duracao = agora - p.data_inicio
        horas = int(duracao.total_seconds() // 3600)
        minutos = int((duracao.total_seconds() % 3600) // 60)
        is_long = duracao.total_seconds() >= 28800  # 8h

        lote_str = p.lote.numero_lote if p.lote else "S/L"
        cultura = p.lote.cultura if p.lote else ""
        target = p.secador.nome if p.secador else (p.silo.name if p.silo else p.tipo_processo)

        desc = f"{lote_str} • {cultura} no {target} — {horas}h{minutos:02d}min em andamento."
        if is_long:
            desc += " — Atenção: já ultrapassou 8 horas."

        dedup = f"proc_active_{p.id}_{agora.hour}"

        Notificacao.objects.update_or_create(
            usuario=usuario,
            dedup_key=dedup,
            defaults={
                'titulo': f"⏱ {p.tipo_processo} prolongada" if is_long else f"▶ {p.tipo_processo} ativa",
                'descricao': desc,
                'tipo': 'Warning' if is_long else 'Info',
                'icone': 'timer_off_rounded' if is_long else 'play_circle_outline_rounded',
                'cor': 'orange' if is_long else 'blue',
                'target': target,
                'is_read': False,
            }
        )

    for p in pausados:
        if not p.data_fim:
            continue
        parado = agora - p.data_fim
        if parado.total_seconds() < 3600:
            continue

        horas = int(parado.total_seconds() // 3600)
        minutos = int((parado.total_seconds() % 3600) // 60)
        target = p.secador.nome if p.secador else (p.silo.name if p.silo else p.tipo_processo)

        Notificacao.objects.update_or_create(
            usuario=usuario,
            dedup_key=f"proc_paused_{p.id}_{agora.hour}",
            defaults={
                'titulo': f"⏸ {p.tipo_processo} pausada",
                'descricao': f"{p.lote.numero_lote if p.lote else 'S/L'} • {p.lote.cultura if p.lote else ''} — parada há {horas}h{minutos:02d}min.",
                'tipo': 'Warning',
                'icone': 'pause_circle_outline_rounded',
                'cor': 'orange',
                'target': target,
                'is_read': False,
            }
        )

    for p in finalizados:
        if not p.data_fim:
            continue
        duracao = p.data_fim - p.data_inicio
        horas = int(duracao.total_seconds() // 3600)
        minutos = int((duracao.total_seconds() % 3600) // 60)
        target = p.secador.nome if p.secador else (p.silo.name if p.silo else p.tipo_processo)

        Notificacao.objects.update_or_create(
            usuario=usuario,
            dedup_key=f"proc_finished_{p.id}_{agora.hour}",
            defaults={
                'titulo': f"✅ {p.tipo_processo} finalizada",
                'descricao': f"{p.lote.numero_lote if p.lote else 'S/L'} • {p.lote.cultura if p.lote else ''} no {target} — {horas}h{minutos:02d}min de operação.",
                'tipo': 'Info',
                'icone': 'check_circle_outline_rounded',
                'cor': 'green',
                'target': target,
                'is_read': False,
            }
        )

    for p in cancelados:
        if not p.data_fim:
            continue
        target = p.secador.nome if p.secador else (p.silo.name if p.silo else p.tipo_processo)

        Notificacao.objects.update_or_create(
            usuario=usuario,
            dedup_key=f"proc_canceled_{p.id}_{agora.hour}",
            defaults={
                'titulo': f"❌ {p.tipo_processo} cancelada",
                'descricao': f"{p.lote.numero_lote if p.lote else 'S/L'} • {p.lote.cultura if p.lote else ''} no {target}.",
                'tipo': 'Warning',
                'icone': 'cancel_rounded',
                'cor': 'red',
                'target': target,
                'is_read': False,
            }
        )

    # Resumo geral
    secagem_count = ativos.filter(tipo_processo='Secagem').count()
    outros_count = ativos.count() - secagem_count
    pausados_count = pausados.count()

    desc_parts = []
    if secagem_count > 0:
        desc_parts.append(f"{secagem_count} secagem(ns)")
    if outros_count > 0:
        desc_parts.append(f"{outros_count} outro(s)")
    resumo_desc = f"{' e '.join(desc_parts)} em andamento. {pausados_count} pausado(s)." if desc_parts else "Nenhum processo ativo."

    tipo = 'Info'
    icone = 'assignment_rounded'
    cor = 'green'
    if ativos.count() == 0 and pausados_count == 0:
        tipo = 'Info'
        icone = 'bedtime_rounded'
        cor = 'grey'
        secadores_livres = Secador.objects.filter(unidade_armazenadora__in=unidades, status='Disponível').count()
        resumo_desc = f"Nenhuma atividade em andamento. {secadores_livres} secador(es) disponível(is)."

    Notificacao.objects.update_or_create(
        usuario=usuario,
        dedup_key=f"proc_summary_{agora.hour}",
        defaults={
            'titulo': '📋 Resumo de processos' if ativos.count() > 0 else '💤 Sem processos ativos',
            'descricao': resumo_desc,
            'tipo': tipo,
            'icone': icone,
            'cor': cor,
            'target': 'Processos',
            'is_read': False,
        }
    )


def gerar_todas_notificacoes(usuario):
    _gerar_notificacoes_fogo(usuario)
    _gerar_notificacoes_processos(usuario)
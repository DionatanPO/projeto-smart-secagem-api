"""
Fonte única da verdade do risco de incêndio.

Limiares espelhados no Flutter em
`lib/core/models/fire_risk_model.dart` — ao alterar aqui, alterar lá.

Sensores cobertos: `sensor_mancal` (temperatura do mancal) e
`sensor_abafando` (gás CO em `dados_extras.nivel_gas` + CO₂ em `co2_ppm`).
"""
import logging
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)

TIPOS_FOGO = ('sensor_mancal', 'sensor_abafando')

# Mancal: temperatura do rolamento
MANCAL_ATENCAO = 75.0
MANCAL_ALERTA = 90.0
MANCAL_EMERGENCIA = 110.0

# Abafamento: gás CO (ppm) em dados_extras.nivel_gas
GAS_ATENCAO = 50.0
GAS_ALERTA = 150.0
GAS_EMERGENCIA = 400.0

# Abafamento: CO₂ (ppm) — ar ambiente ~400-450; alto indica fermentação
CO2_ATENCAO = 1500.0
CO2_ALERTA = 3000.0

# Taxa de subida da temperatura (°C/min)
SUBIDA_ATENCAO = 2.0
SUBIDA_ALERTA = 5.0

NIVEIS = ('safe', 'attention', 'warning', 'critical', 'emergency')
NIVEIS_ALERTA = ('warning', 'critical', 'emergency')


def taxa_subida(telemetrias):
    """°C/min entre a mais antiga e a mais nova. Aceita lista ou queryset."""
    t = list(telemetrias)
    if len(t) < 2:
        return 0.0
    ordenadas = sorted(t, key=lambda x: x.timestamp)
    dt_min = (ordenadas[-1].timestamp - ordenadas[0].timestamp).total_seconds() / 60
    if dt_min <= 0:
        return 0.0
    t0 = ordenadas[0].temperatura or 0
    t1 = ordenadas[-1].temperatura or 0
    return (t1 - t0) / dt_min


def avaliar_risco_incendio(tipo, temperatura, gas_ppm=None, co2_ppm=None, taxa=0.0):
    """Retorna {'nivel': ..., 'score': ...} com os limiares unificados."""
    score = 0

    if tipo == 'sensor_mancal' and temperatura is not None:
        if temperatura >= MANCAL_EMERGENCIA:
            score += 5
        elif temperatura >= MANCAL_ALERTA:
            score += 4
        elif temperatura >= MANCAL_ATENCAO:
            score += 2

    if tipo == 'sensor_abafando':
        if gas_ppm is not None:
            if gas_ppm >= GAS_EMERGENCIA:
                score += 5
            elif gas_ppm >= GAS_ALERTA:
                score += 4
            elif gas_ppm >= GAS_ATENCAO:
                score += 2
        if co2_ppm is not None:
            if co2_ppm >= CO2_ALERTA:
                score += 4
            elif co2_ppm >= CO2_ATENCAO:
                score += 2

    if taxa >= SUBIDA_ALERTA:
        score += 3
    elif taxa >= SUBIDA_ATENCAO:
        score += 1

    if score >= 7:
        nivel = 'emergency'
    elif score >= 5:
        nivel = 'critical'
    elif score >= 3:
        nivel = 'warning'
    elif score >= 1:
        nivel = 'attention'
    else:
        nivel = 'safe'
    return {'nivel': nivel, 'score': score}


def _extrair_gas(telemetria):
    extras = telemetria.dados_extras or {}
    return extras.get('nivel_gas')


def _usuarios_da_unidade(unidade):
    from ..models import User
    return User.objects.filter(
        Q(unidade_armazenadora=unidade) |
        Q(unidades_armazenadoras=unidade) |
        Q(account_type='super_admin')
    ).distinct()


def _notificar(usuario, titulo, descricao, tipo, icone, cor, target, dedup_key):
    from ..models import Notificacao
    Notificacao.objects.update_or_create(
        usuario=usuario,
        dedup_key=dedup_key,
        defaults={
            'titulo': titulo,
            'descricao': descricao,
            'tipo': tipo,
            'icone': icone,
            'cor': cor,
            'target': target,
            'is_read': False,
        },
    )


def processar_telemetria_fogo(telemetria):
    """Avalia uma telemetria recém-criada: notifica e corta em emergência.

    Retorna o nível ('safe'|'attention'|'warning'|'critical'|'emergency').
    Nunca deve estourar exceção para o chamador (gateway).
    """
    from ..models import Telemetry
    try:
        sensor = telemetria.sensor
        if sensor.tipo not in TIPOS_FOGO or not sensor.secador_id:
            return 'safe'

        ultimas = list(Telemetry.objects.filter(sensor=sensor).order_by('-timestamp')[:10])
        if not ultimas:
            return 'safe'
        latest = ultimas[0]
        resultado = avaliar_risco_incendio(
            tipo=sensor.tipo,
            temperatura=latest.temperatura,
            gas_ppm=_extrair_gas(latest),
            co2_ppm=latest.co2_ppm,
            taxa=taxa_subida(ultimas),
        )
        nivel = resultado['nivel']
        if nivel not in NIVEIS_ALERTA:
            return nivel

        secador = sensor.secador
        unidade = secador.unidade_armazenadora
        tipo_label = 'Mancal' if sensor.tipo == 'sensor_mancal' else 'Abafamento'
        temp = latest.temperatura or 0
        gas = _extrair_gas(latest)
        hora = timezone.now().hour
        desc = f"{tipo_label} {sensor.sensor_id}: {temp:.1f}°C no {secador.nome}"
        if gas:
            desc += f" | Gás: {gas:.0f} ppm"
        if latest.co2_ppm:
            desc += f" | CO₂: {latest.co2_ppm:.0f} ppm"
        is_emergency = nivel == 'emergency'

        # Corte automático em emergência, se habilitado nos parâmetros.
        cortados = []
        try:
            params = secador.parametros_automacao
            corte_habilitado = bool(params.ativo and params.corte_emergencia_incendio)
        except Exception:
            params, corte_habilitado = None, False
        if is_emergency and corte_habilitado:
            for motor in secador.motores_aeracao.filter(estado='ligado'):
                motor.estado = 'desligado'
                motor.consumo_atual_kw = 0
                motor.save()
                cortados.append(motor.motor_id)

        for usuario in _usuarios_da_unidade(unidade):
            _notificar(
                usuario,
                '🚨 Emergência de Incêndio' if is_emergency else f'Risco de Incêndio - {nivel.upper()}',
                desc,
                'Critical' if is_emergency or nivel == 'critical' else 'Warning',
                'local_fire_department_rounded' if is_emergency else 'warning_rounded',
                'red' if is_emergency else 'orange',
                secador.nome,
                f"fire_{secador.nome}_{nivel}_{hora}",
            )
            if cortados:
                _notificar(
                    usuario,
                    '✂ Corte automático executado',
                    f"Emergencia no {secador.nome}: motores desligados automaticamente ({', '.join(cortados)}).",
                    'Critical',
                    'power_off_rounded',
                    'red',
                    secador.nome,
                    f"fire_cut_{secador.nome}_{hora}",
                )
        return nivel
    except Exception:
        logger.exception('Falha ao processar telemetria de fogo')
        return 'safe'

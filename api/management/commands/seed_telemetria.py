"""Semeia telemetria horária realista para todos os sensores cadastrados.

Uso:
    python manage.py seed_telemetria --mes 2026-11 --limpar

Gera uma leitura por hora para cada SensorData, respeitando o perfil do tipo
de sensor (temperatura, mancal, abafamento). Os valores ficam sempre dentro da
faixa normal — abaixo dos limiares de alerta de `fire_risk_service.py` — para
não disparar notificações de incêndio. Como usa bulk_create, os signals de
post_save também não são disparados.
"""
import math
import random
from calendar import monthrange
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import F

from api.models import SensorData, Telemetry


# Perfis por ID físico do sensor. `temp_*` e `umid_*` definem o ciclo diário
# (pico por volta das 15h, mínimo por volta das 5h). Os extras fixos entram em
# todas as leituras; mancal/abafamento recebem extras variáveis por leitura.
PERFIS = {
    'TEMP-001': {  # zona superior do secador
        'temp_base': 57.0, 'temp_amp': 7.0,
        'umid_base': 34.0, 'umid_amp': 6.0,
        'extras': {'setpoint': 60.0},
    },
    'TEMP-002': {  # zona média
        'temp_base': 51.0, 'temp_amp': 6.0,
        'umid_base': 37.0, 'umid_amp': 5.5,
        'extras': {'setpoint': 55.0},
    },
    'TEMP-003': {  # zona inferior
        'temp_base': 43.0, 'temp_amp': 5.0,
        'umid_base': 41.0, 'umid_amp': 5.0,
        'extras': {'setpoint': 45.0},
    },
    'MANC-001': {  # mancal do ventilador (limite de atenção: 75 °C)
        'temp_base': 48.0, 'temp_amp': 12.0,
        'umid_base': 30.0, 'umid_amp': 4.0,
        'extras': {},
    },
    'ABAF-001': {  # exaustão / abafamento (CO e CO₂ baixos)
        'temp_base': 39.0, 'temp_amp': 6.0,
        'umid_base': 28.0, 'umid_amp': 4.5,
        'extras': {},
    },
    'TEMP-004': {  # plenum de ar quente
        'temp_base': 64.0, 'temp_amp': 9.0,
        'umid_base': 22.0, 'umid_amp': 4.0,
        'extras': {'setpoint': 70.0},
    },
    'TEMP-005': {  # temperatura ambiente externa
        'temp_base': 24.0, 'temp_amp': 6.5,
        'umid_base': 58.0, 'umid_amp': 12.0,
        'extras': {},
    },
}

# Perfil genérico para sensores que não estejam mapeados acima.
PERFIL_PADRAO = {
    'temp_base': 30.0, 'temp_amp': 5.0,
    'umid_base': 45.0, 'umid_amp': 6.0,
    'extras': {},
}


def ciclo_diario(hora):
    """Seno com pico às 15h e mínimo às 3h."""
    return math.sin(2 * math.pi * (hora - 9) / 24)


class Command(BaseCommand):
    help = 'Gera telemetria horária realista para um mês (padrão: novembro/2026)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mes', default='2026-11',
            help='Mês no formato YYYY-MM (padrão: 2026-11)',
        )
        parser.add_argument(
            '--limpar', action='store_true',
            help='Apaga TODA a telemetria existente antes de gerar',
        )
        parser.add_argument(
            '--seed', type=int, default=42,
            help='Semente do gerador aleatório (padrão: 42)',
        )

    def handle(self, *args, **options):
        try:
            ano, mes = (int(p) for p in options['mes'].split('-'))
            dias_no_mes = monthrange(ano, mes)[1]
        except (ValueError, TypeError):
            raise CommandError('Use --mes no formato YYYY-MM (ex.: 2026-11).')

        random.seed(options['seed'])
        sensores = list(SensorData.objects.all().order_by('id'))
        if not sensores:
            raise CommandError('Nenhum sensor cadastrado. Cadastre sensores antes de gerar telemetria.')

        if options['limpar']:
            apagados, _ = Telemetry.objects.all().delete()
            self.stdout.write(f'Telemetria anterior removida: {apagados} registro(s).')

        inicio = datetime(ano, mes, 1, 0, 0, 0)
        total = dias_no_mes * 24 * len(sensores)
        self.stdout.write(
            f'Gerando {total} leituras para {len(sensores)} sensor(es) '
            f'em {mes:02d}/{ano}...'
        )

        lote = []
        criados = 0
        with transaction.atomic():
            for sensor in sensores:
                perfil = PERFIS.get(sensor.sensor_id, PERFIL_PADRAO)
                for dia in range(dias_no_mes):
                    for hora in range(24):
                        ts = inicio + timedelta(days=dia, hours=hora)
                        lote.append(self._montar_leitura(sensor, perfil, ts))
                # grava sensor por sensor para limitar memória
                Telemetry.objects.bulk_create(lote, batch_size=1000)
                criados += len(lote)
                lote = []

            # auto_now_add sobrescreve received_at no insert; alinha com a coleta
            Telemetry.objects.filter(
                timestamp__year=ano, timestamp__month=mes
            ).update(received_at=F('timestamp'))

        self.stdout.write(self.style.SUCCESS(
            f'{criados} leitura(s) de telemetria criada(s) para {mes:02d}/{ano}.'
        ))

    def _montar_leitura(self, sensor, perfil, ts):
        hora = ts.hour
        ciclo = ciclo_diario(hora)
        # ruído leve para não ficar uma senoide perfeita
        ruido_temp = random.uniform(-0.8, 0.8)
        temperatura = perfil['temp_base'] + perfil['temp_amp'] * ciclo + ruido_temp
        # umidade varia ao contrário da temperatura
        umidade = perfil['umid_base'] - (perfil['umid_amp'] / 2) * ciclo + random.uniform(-1.5, 1.5)

        extras = dict(perfil['extras'])
        co2_ppm = None

        if sensor.tipo == 'sensor_mancal':
            # mantém abaixo do limite de atenção (75 °C)
            temperatura = min(temperatura, 68.0)
            operando = 6 <= hora <= 22
            rpm = random.randint(1250, 1750) if operando else 0
            vibracao = round(random.uniform(0.18, 0.45) if operando else random.uniform(0.05, 0.15), 2)
            extras.update({'rpm': rpm, 'vibracao': vibracao})

        elif sensor.tipo == 'sensor_abafando':
            # CO abaixo do limite de atenção (50 ppm) e CO₂ abaixo de 1500 ppm
            extras['nivel_gas'] = round(max(1.0, 6.0 + 5.0 * ciclo + random.uniform(-2.0, 2.0)), 1)
            extras['umidade_ar'] = round(umidade, 1)
            co2_ppm = round(max(380.0, 450.0 + 140.0 * ciclo + random.uniform(-40.0, 40.0)), 0)

        return Telemetry(
            sensor=sensor,
            temperatura=round(temperatura, 1),
            umidade=round(max(1.0, umidade), 1),
            co2_ppm=co2_ppm,
            dados_extras=extras,
            timestamp=ts,
            received_at=ts,
        )

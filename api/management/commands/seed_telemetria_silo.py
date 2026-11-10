"""Cria sensores de silo (temperatura por nível + umidade) e semeia a
telemetria horária de um mês para eles.

Uso:
    python manage.py seed_telemetria_silo --mes 2026-11

Idempotente: os sensores são criados com get_or_create pelo ID físico e a
telemetria do mês informado para esses sensores é substituída. A telemetria
do secador NÃO é tocada.
"""
import math
import random
from calendar import monthrange
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import F

from api.models import Silo, SensorData, Telemetry


# Níveis monitorados por tipo de silo. `lag_h` desloca o pico diário: as
# camadas mais profundas respondem com atraso e com menor amplitude.
PERFIS_POR_TIPO = {
    'armazenamento': [
        {'nivel': 'topo', 'profundidade_m': 0.5, 'temp_base': 26.5, 'temp_amp': 3.0, 'lag_h': 0},
        {'nivel': 'superior', 'profundidade_m': 4.0, 'temp_base': 24.5, 'temp_amp': 2.0, 'lag_h': 2},
        {'nivel': 'intermediario', 'profundidade_m': 8.0, 'temp_base': 22.8, 'temp_amp': 1.0, 'lag_h': 4},
        {'nivel': 'fundo', 'profundidade_m': 12.0, 'temp_base': 21.5, 'temp_amp': 0.4, 'lag_h': 6},
    ],
    'pulmao': [
        {'nivel': 'topo', 'profundidade_m': 0.5, 'temp_base': 25.5, 'temp_amp': 3.2, 'lag_h': 0},
        {'nivel': 'fundo', 'profundidade_m': 3.0, 'temp_base': 22.0, 'temp_amp': 0.8, 'lag_h': 3},
    ],
}

# Umidade intersticial do grão: estável, com leve variação diária.
UMIDADE_POR_TIPO = {
    'armazenamento': {'base': 61.0, 'amp': 3.0, 'lag_h': 1},
    'pulmao': {'base': 64.0, 'amp': 3.5, 'lag_h': 1},
}


def ciclo_diario(hora, lag_h=0):
    """Seno com pico às 15h (deslocado por `lag_h`)."""
    return math.sin(2 * math.pi * (hora - lag_h - 9) / 24)


class Command(BaseCommand):
    help = 'Cria sensores de silo e gera telemetria mensal (padrão: novembro/2026)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mes', default='2026-11',
            help='Mês no formato YYYY-MM (padrão: 2026-11)',
        )
        parser.add_argument(
            '--seed', type=int, default=42,
            help='Semente do gerador aleatório (padrão: 42)',
        )
        parser.add_argument(
            '--recriar-sensores', action='store_true',
            help='Apaga os sensores de silo existentes (e sua telemetria) antes de recriar',
        )

    def handle(self, *args, **options):
        try:
            ano, mes = (int(p) for p in options['mes'].split('-'))
            dias_no_mes = monthrange(ano, mes)[1]
        except (ValueError, TypeError):
            raise CommandError('Use --mes no formato YYYY-MM (ex.: 2026-11).')

        silos = list(Silo.objects.all().order_by('id'))
        if not silos:
            raise CommandError('Nenhum silo cadastrado. Cadastre silos antes de gerar telemetria.')

        if options['recriar_sensores']:
            SensoresSilo = SensorData.objects.filter(silo__isnull=False)
            apagados = SensoresSilo.count()
            SensoresSilo.delete()
            self.stdout.write(f'Sensores de silo removidos: {apagados}.')

        random.seed(options['seed'])
        planos = []  # (sensor, perfil)
        criados_sensores = 0

        for silo in silos:
            niveis = PERFIS_POR_TIPO.get(silo.tipo, PERFIS_POR_TIPO['armazenamento'])
            for idx, nivel in enumerate(niveis, start=1):
                sensor_id = f'SILO{silo.id}-TEMP-{idx:02d}'
                sensor, criado = SensorData.objects.get_or_create(
                    sensor_id=sensor_id,
                    defaults={
                        'tipo': 'sensor_temperatura',
                        'silo': silo,
                        'unidade_armazenadora': silo.unidade_armazenadora,
                        'description': (
                            f'Temperatura {nivel["nivel"]} - {silo.name} '
                            f'({nivel["profundidade_m"]} m)'
                        ),
                        'status': 'ativo',
                    },
                )
                criados_sensores += int(criado)
                planos.append((sensor, {'tipo': 'temperatura', **nivel}))

            umid = UMIDADE_POR_TIPO.get(silo.tipo, UMIDADE_POR_TIPO['armazenamento'])
            sensor_id = f'SILO{silo.id}-UMID-01'
            sensor, criado = SensorData.objects.get_or_create(
                sensor_id=sensor_id,
                defaults={
                    'tipo': 'sensor_umidade',
                    'silo': silo,
                    'unidade_armazenadora': silo.unidade_armazenadora,
                    'description': f'Umidade intersticial - {silo.name}',
                    'status': 'ativo',
                },
            )
            criados_sensores += int(criado)
            planos.append((sensor, {'tipo': 'umidade', **umid}))

        self.stdout.write(
            f'Sensores de silo: {len(planos)} configurado(s) '
            f'({criados_sensores} novo(s)).'
        )

        # Substitui apenas a telemetria dos sensores de silo no mês pedido.
        sensores_ids = [s.id for s, _ in planos]
        removidos, _ = Telemetry.objects.filter(
            sensor_id__in=sensores_ids,
            timestamp__year=ano, timestamp__month=mes,
        ).delete()
        if removidos:
            self.stdout.write(f'Telemetria de silo do mês removida: {removidos} registro(s).')

        inicio = datetime(ano, mes, 1, 0, 0, 0)
        total = dias_no_mes * 24 * len(planos)
        self.stdout.write(f'Gerando {total} leituras de silo em {mes:02d}/{ano}...')

        with transaction.atomic():
            for sensor, perfil in planos:
                lote = []
                for dia in range(dias_no_mes):
                    for hora in range(24):
                        ts = inicio + timedelta(days=dia, hours=hora)
                        lote.append(self._montar_leitura(sensor, perfil, ts))
                Telemetry.objects.bulk_create(lote, batch_size=1000)

            Telemetry.objects.filter(
                sensor_id__in=sensores_ids,
                timestamp__year=ano, timestamp__month=mes,
            ).update(received_at=F('timestamp'))

        self.stdout.write(self.style.SUCCESS(
            f'{total} leitura(s) de silo criada(s) para {mes:02d}/{ano}.'
        ))

    def _montar_leitura(self, sensor, perfil, ts):
        ciclo = ciclo_diario(ts.hour, perfil.get('lag_h', 0))

        if perfil['tipo'] == 'temperatura':
            temperatura = perfil['temp_base'] + perfil['temp_amp'] * ciclo + random.uniform(-0.25, 0.25)
            return Telemetry(
                sensor=sensor,
                temperatura=round(temperatura, 1),
                umidade=None,
                co2_ppm=None,
                dados_extras={
                    'nivel': perfil['nivel'],
                    'profundidade_m': perfil['profundidade_m'],
                },
                timestamp=ts,
                received_at=ts,
            )

        # sensor de umidade: sem temperatura própria
        umidade = perfil['base'] - (perfil['amp'] / 2) * ciclo + random.uniform(-1.0, 1.0)
        return Telemetry(
            sensor=sensor,
            temperatura=None,
            umidade=round(max(1.0, umidade), 1),
            co2_ppm=None,
            dados_extras={'nivel': 'intermediario'},
            timestamp=ts,
            received_at=ts,
        )

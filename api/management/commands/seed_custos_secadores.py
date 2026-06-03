from django.core.management.base import BaseCommand
from api.models import Secador


class Command(BaseCommand):
    help = 'Preenche dados fictícios reais de custos para secadores existentes'

    def handle(self, *args, **options):
        updated = 0
        for s in Secador.objects.all():
            data = self._get_cost_data(s)
            if data:
                for key, val in data.items():
                    setattr(s, key, val)
                s.save()
                updated += 1
                self.stdout.write(f'  OK  {s.nome} (id={s.id})')
        self.stdout.write(self.style.SUCCESS(f'{updated} secador(es) atualizado(s).'))

    def _get_cost_data(self, s):
        tipo = s.tipo
        fonte = s.fonte_calor
        cap = s.capacidade

        base = {
            'custo_aquisicao': None,
            'valor_residual': None,
            'vida_util_anos': 20,
            'custo_instalacao': None,
            'custo_manutencao_anual': None,
            'consumo_combustivel_hora': None,
            'preco_combustivel': None,
            'consumo_energia_kwh': None,
            'preco_kwh': 0.5432,
            'custo_mao_obra_hora': None,
        }

        # Custo de aquisição base por tipo
        if tipo == 'Coluna':
            base['custo_aquisicao'] = round(180000 + cap * 3500, 2)
            base['custo_instalacao'] = round(base['custo_aquisicao'] * 0.08, 2)
            base['custo_manutencao_anual'] = round(base['custo_aquisicao'] * 0.035, 2)
        elif tipo == 'Cascata':
            base['custo_aquisicao'] = round(250000 + cap * 4000, 2)
            base['custo_instalacao'] = round(base['custo_aquisicao'] * 0.10, 2)
            base['custo_manutencao_anual'] = round(base['custo_aquisicao'] * 0.04, 2)
        elif tipo == 'Fluxo Contínuo':
            base['custo_aquisicao'] = round(350000 + cap * 5000, 2)
            base['custo_instalacao'] = round(base['custo_aquisicao'] * 0.12, 2)
            base['custo_manutencao_anual'] = round(base['custo_aquisicao'] * 0.045, 2)
        elif tipo == 'Batelada':
            base['custo_aquisicao'] = round(120000 + cap * 2800, 2)
            base['custo_instalacao'] = round(base['custo_aquisicao'] * 0.06, 2)
            base['custo_manutencao_anual'] = round(base['custo_aquisicao'] * 0.03, 2)
        else:
            base['custo_aquisicao'] = round(200000 + cap * 3000, 2)
            base['custo_instalacao'] = round(base['custo_aquisicao'] * 0.08, 2)
            base['custo_manutencao_anual'] = round(base['custo_aquisicao'] * 0.035, 2)

        base['valor_residual'] = round(base['custo_aquisicao'] * 0.12, 2)

        # Consumo de combustível por fonte de calor
        if fonte == 'Lenha':
            base['consumo_combustivel_hora'] = round(cap * 55.0, 2)
            base['preco_combustivel'] = 180.00
        elif fonte == 'Gás GLP':
            base['consumo_combustivel_hora'] = round(cap * 8.5, 2)
            base['preco_combustivel'] = 7.50
        elif fonte == 'Biomassa':
            base['consumo_combustivel_hora'] = round(cap * 65.0, 2)
            base['preco_combustivel'] = 120.00
        elif fonte == 'Elétrico':
            base['consumo_combustivel_hora'] = 0
            base['preco_combustivel'] = 0

        # Consumo de energia
        if fonte == 'Elétrico':
            base['consumo_energia_kwh'] = round(cap * 45.0, 2)
        else:
            base['consumo_energia_kwh'] = round(cap * 15.0 + 8.0, 2)

        # Mão de obra
        if cap <= 30:
            base['custo_mao_obra_hora'] = 18.50
        elif cap <= 80:
            base['custo_mao_obra_hora'] = 22.00
        else:
            base['custo_mao_obra_hora'] = 28.75

        # Remove None values (avoid overwriting existing fields with null)
        return {k: v for k, v in base.items() if v is not None}

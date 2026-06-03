from decimal import Decimal


def calcular_custos_processo(processo):
    """Calcula custos de um processo de secagem finalizado."""
    if not processo.data_fim or not processo.data_inicio:
        return None

    duracao = processo.data_fim - processo.data_inicio
    duracao_horas = duracao.total_seconds() / 3600
    duracao_dias = duracao_horas / 24
    secador = processo.secador

    custo_combustivel = 0.0
    custo_energia = 0.0
    custo_mao_obra = 0.0
    custo_manutencao = 0.0
    custo_depreciacao = 0.0

    if secador:
        if secador.consumo_combustivel_hora and secador.preco_combustivel:
            custo_combustivel = float(
                secador.consumo_combustivel_hora * float(secador.preco_combustivel) * duracao_horas
            )
        if secador.consumo_energia_kwh and secador.preco_kwh:
            custo_energia = float(
                secador.consumo_energia_kwh * float(secador.preco_kwh) * duracao_horas
            )
        if secador.custo_mao_obra_hora:
            custo_mao_obra = float(secador.custo_mao_obra_hora) * duracao_horas
        if secador.custo_manutencao_anual:
            custo_manutencao = float(secador.custo_manutencao_anual) / 365 * duracao_dias
        if secador.custo_aquisicao and secador.valor_residual and secador.vida_util_anos:
            custo_depreciacao = (
                (float(secador.custo_aquisicao) - float(secador.valor_residual))
                / secador.vida_util_anos / 365 * duracao_dias
            )

    custo_total = custo_combustivel + custo_energia + custo_mao_obra + custo_manutencao + custo_depreciacao

    return {
        'duracao_horas': round(duracao_horas, 2),
        'duracao_dias': round(duracao_dias, 2),
        'custo_combustivel': round(custo_combustivel, 2),
        'custo_energia': round(custo_energia, 2),
        'custo_mao_obra': round(custo_mao_obra, 2),
        'custo_manutencao': round(custo_manutencao, 2),
        'custo_depreciacao': round(custo_depreciacao, 2),
        'custo_total': round(custo_total, 2),
        'custo_por_hora': round(custo_total / duracao_horas, 2) if duracao_horas > 0 else 0,
    }

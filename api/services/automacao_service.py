"""
Critérios de fim de secagem (lote 1, literatura BR).

- A massa/exaustão tende a se equilibrar com o ar de secagem no fim
  (UFV): delta plenum–exaustão pequeno = grão parou de ceder água.
- O grão deve sair frio, 5–10 °C acima da temperatura ambiente
  (Weber/GSI): saída quente = resfriamento insuficiente.
"""


def avaliar_fim_secagem(*, delta_exaustao_fim=20.0, saida_acima_ambiente_max=10.0,
                        temp_plenum=None, temp_exaustao=None,
                        temp_saida_grao=None, temp_ext=None):
    """Retorna {'fim': bool, 'motivos': [...], 'checks': {...}}.

    `fim` é True quando QUALQUER critério é atendido. Critérios sem
    leitura disponível são ignorados (retornam None em checks).
    """
    motivos = []
    checks = {'delta_exaustao': None, 'saida_acima_ambiente': None}

    if temp_plenum is not None and temp_exaustao is not None:
        delta = temp_plenum - temp_exaustao
        checks['delta_exaustao'] = round(delta, 1)
        if delta < delta_exaustao_fim:
            motivos.append(
                f'Delta plenum–exaustão {delta:.1f}°C < {delta_exaustao_fim:.1f}°C: massa parou de ceder água')

    if temp_saida_grao is not None and temp_ext is not None:
        acima = temp_saida_grao - temp_ext
        checks['saida_acima_ambiente'] = round(acima, 1)
        if acima <= saida_acima_ambiente_max:
            motivos.append(
                f'Saída {temp_saida_grao:.1f}°C a {acima:.1f}°C do ambiente (limite {saida_acima_ambiente_max:.1f}°C): grão frio')

    return {'fim': bool(motivos), 'motivos': motivos, 'checks': checks}

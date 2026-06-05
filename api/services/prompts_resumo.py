"""
PROMPTS PARA GERACAO DE RESUMOS OPERACIONAIS VIA LLM

Cada prompt e auto-contido e deve ser enviado ao modelo LLM
junto com os dados do contexto (get_ai_context).

Uso:
  contexto = get_ai_context(request.user)
  prompt = PROMPTS["executivo_24h"]["prompt"]
  mensagem = prompt + "\n\n### DADOS DO CONTEXTO:\n\n" + contexto
  resposta = send_chat_request(mensagem, ...)
"""

PROMPT_EXECUTIVO_24H = """### TITULO: Relatorio Executivo — Panorama Geral das Ultimas 24h

### OBJETIVO:
Gerar um resumo executivo claro e direto do estado operacional da unidade
armazenadora nas ultimas 24 horas. O relatorio deve destacar os numeros
mais importantes, alertas criticos e recomendacoes imediatas para o gestor.

### DADOS FORNECIDOS (via contexto):
- resumo_operacional (processos ativos, finalizados hoje, secadores
  disponiveis, silos disponiveis, grao armazenado total, sensores ativos)
- alertas (processos pausados, secadores em manutencao, silos >95%,
  lotes parados >30 dias)
- processos_completos (cada processo com atividade, status, duracao,
  lote, secador, silo associados)
- silos_dados (nome, capacidade, ocupacao %, status)
- secadores_dados (nome, tipo, status, custo operacional/hora)

### INSTRUCOES PARA O LLM:
1. Analise os dados de resumo_operacional e apresente os principais
   indicadores de forma destacada.
2. Liste os alertas que exigem acao imediata (prioridade: processo
   pausado > silo critico > lote parado).
3. Identifique gargalos visiveis: muitos processos pausados, secadores
   indisponiveis, silos proximos do limite.
4. Se houver dados de telemetria nos sensores, mencione leituras
   atipicas (temperatura elevada, umidade critica).
5. Encerre com 1-3 recomendacoes objetivas para o gestor.
6. Use linguagem direta, bullet points e secoes claras.

### FORMATO DE SAIDA ESPERADO (preencher com dados reais):

--- INICIO DO RELATORIO ---
RELATORIO EXECUTIVO — {DATA_REFERENCIA}

RESUMO DO PERIODO:
- Processos ativos: {X} | Finalizados hoje: {Y}
- Secadores disponiveis: {X} | Em manutencao: {Y}
- Silos disponiveis: {X} | Ocupacao media: {Y}%
- Grao armazenado total: {X.XXX} kg
- Sensores ativos: {X}

ALERTAS CRITICOS:
- {alerta mais grave}
- {alerta secundario}

GARGALOS IDENTIFICADOS:
- {descricao do gargalo}

RECOMENDACOES:
1. {recomendacao 1}
2. {recomendacao 2}
--- FIM DO RELATORIO ---
"""

PROMPT_CUSTOS_SECAGEM = """### TITULO: Relatorio de Custos de Secagem — Analise Financeira Detalhada

### OBJETIVO:
Produzir uma analise financeira completa dos custos de secagem,
cruzando dados de processos finalizados, secadores utilizados e
custos operacionais. O relatorio deve permitir ao gestor identificar
oportunidades de reducao de custos e comparar performance entre
secadores.

### DADOS FORNECIDOS (via contexto):
- custos_secagem.processos (cada um com: lote, cultura, secador,
  duracao_h, custo_combustivel, custo_energia, custo_mao_obra,
  custo_manutencao, custo_depreciacao, custo_total, custo_por_hora)
- custos_secagem.totalizador (totais consolidados de cada rubrica:
  total_combustivel, total_energia, total_mao_obra, total_manutencao,
  total_depreciacao, total_geral)
- secadores_dados (nome, tipo, capacidade, combustivel, status,
  custo_operacional_hora)
- processos_completos (para cruzar tipo de grao vs custo)

### INSTRUCOES PARA O LLM:
1. Apresente o custo total do periodo e o breakdown percentual
   (combustivel, energia, mao-de-obra, manutencao, depreciacao).
2. Calcule o custo medio por hora e por tonelada processada.
3. Compare o desempenho entre secadores disponiveis: qual teve
   menor/maior custo por hora ou por lote.
4. Se houver dados de fonte de calor (lenha vs GLP vs biomassa),
   faca uma analise comparativa de custo entre elas.
5. Identifique processos com custo muito acima da media e sugira
   investigacao.
6. Inclua projecao: se o ritmo atual se mantiver, qual sera o
   custo acumulado no mes.

### FORMATO DE SAIDA ESPERADO (preencher com dados reais):

--- INICIO DO RELATORIO ---
RELATORIO DE CUSTOS DE SECAGEM

CUSTO TOTAL DO PERIODO: R$ {X.XXX,XX}
- Combustivel: R$ {X} ({Y}%)
- Energia: R$ {X} ({Y}%)
- Mao-de-obra: R$ {X} ({Y}%)
- Manutencao: R$ {X} ({Y}%)
- Depreciacao: R$ {X} ({Y}%)

CUSTOS MEDIOS:
- Custo medio / hora: R$ {X,XX}
- Custo medio / tonelada: R$ {X,XX}
- Total de horas de secagem: {X}h

COMPARATIVO ENTRE SECADORES:
| Secador | Tipo | Combustivel | Custo/h | Horas | Custo total |
| {nome}  | {tipo} | {fonte} | R$ {X} | {Y}h | R$ {Z} |

PROCESSOS FORA DA CURVA:
- {lote}: custo {X}% acima da media — causa provavel: {causa}

PROJECAO MENSAL:
- Custo acumulado ate agora: R$ {X}
- Projecao fim do mes: R$ {Y}
- Orcamento vs realizado: {+/-} {Z}%
--- FIM DO RELATORIO ---
"""

PROMPT_SAUDE_LOTES = """### TITULO: Relatorio de Saude dos Lotes — Risco, Qualidade e Tempo de Estoque

### OBJETIVO:
Analisar todos os lotes ativos na unidade armazenadora, identificando
riscos de deterioracao, lotes parados ha muito tempo, umidade fora
do padrao e necessidade de intervencao. Este relatorio e critico
para garantir a qualidade do grao armazenado e evitar perdas.

### DADOS FORNECIDOS (via contexto):
- lotes (cada um com: numero, cultura, safra, peso_inicial_kg,
  peso_final_kg, umidade_inicial_pct, umidade_final_pct, entrada,
  saida, dias_em_estoque, status, cliente)
- processos_completos (para cruzar se o lote passou por secagem)
- alertas (especialmente lotes parados >30 dias)
- silos_dados (para saber onde cada lote esta armazenado)

### INSTRUCOES PARA O LLM:
1. Classifique os lotes por nivel de risco:
   - RISCO ALTO: >45 dias sem finalizar OU umidade inicial >16%
   - RISCO MEDIO: 30-45 dias OU umidade entre 14-16%
   - RISCO BAIXO: <30 dias E umidade <14%
2. Liste os lotes que ja deveriam ter passado por secagem mas nao
   tem processo associado (baseado na umidade inicial alta).
3. Calcule a quebra tecnica (peso_inicial - peso_final) dos lotes
   que ja passaram por secagem e destaque os atipicos.
4. Para lotes com cliente associado, mencione o cliente.
5. Agrupe por cultura e safra para visao consolidada.
6. Encerre com recomendacoes priorizadas por risco.

### FORMATO DE SAIDA ESPERADO (preencher com dados reais):

--- INICIO DO RELATORIO ---
RELATORIO DE SAUDE DOS LOTES

LOTES SEGUROS (RISCO BAIXO) — {X} lotes:
- {lote} — {cultura} — {dias} dias — umidade {X}%

ATENCAO (RISCO MEDIO) — {Y} lotes:
- {lote} — {cultura} — {dias} dias — umidade {X}%

CRITICOS (RISCO ALTO) — {Z} lotes:
- {lote} — {cultura} — {dias} dias — umidade {X}%
  Motivo: {dias sem finalizar / umidade excessiva}

QUEBRA TECNICA NA SECAGEM:
- Media geral: {X}%
- Maior quebra: {lote} — {Y}%
- Menor quebra: {lote} — {W}%

RESUMO POR CULTURA:
| Cultura | Lotes | Volume (kg) | Umidade media | Dias medio |
| {Soja}  | {X}   | {kg}        | {Y}%          | {Z}d       |

RECOMENDACOES:
1. {prioridade maxima}
2. {prioridade media}
3. {prioridade baixa}
--- FIM DO RELATORIO ---
"""

PROMPT_OCUPACAO_ARMAZENAGEM = """### TITULO: Relatorio de Ocupacao e Capacidade de Armazenagem

### OBJETIVO:
Fornecer uma visao completa da capacidade de armazenagem da unidade:
ocupacao atual dos silos, tendencia de ocupacao, projecao de
saturacao e recomendacoes para gestao de espaco. Essencial para
planejamento logistico e tomada de decisao sobre recebimento de
novas cargas.

### DADOS FORNECIDOS (via contexto):
- silos_dados (nome, capacidade_kg, ocupacao_kg, ocupacao_pct, status)
- resumo_operacional (grao armazenado total, silos disponiveis)
- lotes (para estimar entrada/saida recente)
- alertas (silos com ocupacao >95%)
- processos (para identificar movimentacao recente)

### INSTRUCOES PARA O LLM:
1. Apresente o panorama geral: capacidade total disponivel vs ocupada.
2. Classifique cada silo por faixa de ocupacao:
   - CRITICO: >90%
   - ALERTA: 75-90%
   - OK: 50-75%
   - FOLGA: <50%
3. Se houver dados de entrada/saida recente nos lotes, estime
   a tendencia de ocupacao (subindo/estavel/descendo).
4. Projete quantos dias restam ate a saturacao total (100%) com
   base no ritmo atual de entrada de graos.
5. Identifique silos disponiveis para novos lotes.
6. Se houver silos em manutencao/desativados, destaque o impacto
   na capacidade total.

### FORMATO DE SAIDA ESPERADO (preencher com dados reais):

--- INICIO DO RELATORIO ---
RELATORIO DE OCUPACAO — CAPACIDADE DE ARMAZENAGEM

PANORAMA GERAL:
- Capacidade total: {X.XXX.XXX} kg
- Ocupado: {Y.YYY.YYY} kg ({Z}%)
- Disponivel: {W.WWW.WWW} kg
- Silos cadastrados: {X} | Ativos: {Y} | Manutencao: {Z}

SILOS CRITICOS (>90%):
| Silo | Ocupacao | Capacidade (kg) | Status |

SILOS EM ALERTA (75-90%):
| Silo | Ocupacao | Capacidade (kg) | Status |

SILOS DISPONIVEIS (<50%):
| Silo | Ocupacao | Capacidade disponivel (kg) |

TENDENCIA E PROJECAO:
- Ritmo de entrada estimado: {X} kg/dia
- Ritmo de saida estimado: {Y} kg/dia
- Saldo diario: {+/- Z} kg/dia
- Dias ate saturacao total: {W} dias
- Projecao de ocupacao em 7 dias: {V}%

RECOMENDACOES:
1. {rotacao de estoque / novo lote em silo X}
2. {priorizar saida de lotes parados}
3. {avaliar necessidade de expansao}
--- FIM DO RELATORIO ---
"""

PROMPT_GARGALOS_OPERACIONAIS = """### TITULO: Relatorio de Gargalos Operacionais — Diagnostico de Fluxo

### OBJETIVO:
Diagnosticar gargalos no fluxo de beneficiamento da unidade
armazenadora. O relatorio cruza dados de processos ativos/pausados,
disponibilidade de secadores e silos, lotes aguardando e alertas
para identificar onde o fluxo esta travando e recomendar acoes
corretivas.

### DADOS FORNECIDOS (via contexto):
- processos (tipo_processo, status, data_inicio, data_fim, duracao,
  lote associado, secador associado, silo associado)
- secadores (nome, status, capacidade, custo_operacional_hora)
- silos (nome, ocupacao_pct, status)
- lotes (numero, cultura, status, dias_em_estoque)
- alertas (processos pausados, secadores em manutencao, silos
  criticos, lotes parados)
- resumo_operacional (processos ativos, secadores disponiveis,
  silos disponiveis)

### INSTRUCOES PARA O LLM:
1. Identifique onde esta o gargalo principal analisando:
   a) Processos pausados (o que esta travando?)
   b) Secadores ocupados vs disponiveis (ha fila de secagem?)
   c) Silos cheios (impedindo novo recebimento?)
   d) Lotes parados sem processo associado
2. Calcule o tempo medio de espera entre etapas (ex: da entrada
   do lote ate o inicio da secagem).
3. Mapeie o fluxo: RECEPCAO -> SECAGEM -> ARMAZENAMENTO -> EXPEDICAO
   e aponte onde ha acumulo.
4. Se houver multiplos secadores, identifique se a distribuicao
   de carga entre eles e equilibrada.
5. Sugira acoes especificas para destravar cada gargalo.

### FORMATO DE SAIDA ESPERADO (preencher com dados reais):

--- INICIO DO RELATORIO ---
RELATORIO DE GARGALOS OPERACIONAIS

DIAGNOSTICO DO FLUXO:

RECEPCAO:
- Lotes aguardando processo inicial: {X}
- Status: {normal / gargalo}

SECAGEM:
- Processos de secagem ativos: {X}
- Processos pausados: {Y} (ha {Z}h)
- Secadores disponiveis: {W} | Ocupados: {V}
- Lotes aguardando secagem: {U}
- Tempo medio de espera na fila: {T}h

ARMAZENAMENTO:
- Silos disponiveis: {X}
- Silos criticos (>90%): {Y}
- Lotes armazenados sem processo de saida: {Z}

EXPEDICAO:
- Lotes prontos para despacho: {X}
- Status: {normal / gargalo}

INDICADORES DE FLUXO:
- Tempo medio entrada -> secagem: {X}h
- Tempo medio secagem -> armazenamento: {Y}h
- Tempo medio armazenamento -> expedicao: {Z}d
- Throughput diario estimado: {W} kg/dia

GARGALO PRINCIPAL:
{etapa} — {descricao do gargalo}

ACOES CORRETIVAS:
1. {acao 1}
2. {acao 2}
3. {acao 3}
--- FIM DO RELATORIO ---
"""

# -- MAPA PARA FACIL ACESSO -------------------------------------
PROMPTS = {
    "executivo_24h": {
        "nome": "Relatorio Executivo 24h",
        "descricao": "Panorama geral da unidade nas ultimas 24h com alertas e recomendacoes",
        "prompt": PROMPT_EXECUTIVO_24H,
    },
    "custos_secagem": {
        "nome": "Relatorio de Custos de Secagem",
        "descricao": "Analise financeira detalhada dos custos de secagem por processo e secador",
        "prompt": PROMPT_CUSTOS_SECAGEM,
    },
    "saude_lotes": {
        "nome": "Relatorio de Saude dos Lotes",
        "descricao": "Classificacao de risco dos lotes por tempo de estoque, umidade e deterioracao",
        "prompt": PROMPT_SAUDE_LOTES,
    },
    "ocupacao_armazenagem": {
        "nome": "Relatorio de Ocupacao e Capacidade",
        "descricao": "Analise da capacidade de armazenagem, ocupacao dos silos e projecao de saturacao",
        "prompt": PROMPT_OCUPACAO_ARMAZENAGEM,
    },
    "gargalos_operacionais": {
        "nome": "Relatorio de Gargalos Operacionais",
        "descricao": "Diagnostico completo do fluxo de beneficiamento identificando gargalos e acoes corretivas",
        "prompt": PROMPT_GARGALOS_OPERACIONAIS,
    },
}

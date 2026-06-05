"""
Serviço para comunicação com a Foundation AI local.
Encaminha requisições do Django para a API de IA rodando localmente.
"""
import json
import os
import requests

# URL completa do endpoint de chat da Foundation AI (outra API Django)
FOUNDATION_AI_CHAT_URL = os.environ.get('FOUNDATION_AI_CHAT_URL', 'http://127.0.0.1:8001/api/chat/')

TIMEOUT_SECONDS = int(os.environ.get('FOUNDATION_AI_TIMEOUT', 300))


def stream_chat_request(prompt, image_base64=None, history=None, use_rag=True, temperature=0.1, system_prompt=None):
    """
    Envia uma requisição de chat para a Foundation AI local e gera respostas em stream.

    Args:
        prompt (str): Mensagem/pergunta do usuário.
        image_base64 (str|None): Imagem em Base64.
        history (list|None): Histórico da conversa.
        use_rag (bool): Se a IA deve consultar a base interna.
        temperature (float): Criatividade da resposta.
        system_prompt (str|None): Instrução de sistema.

    Yields:
        dict: Evento no formato {"type": "...", "content": "..."}
    """
    payload = {
        "prompt": prompt,
        "use_rag": use_rag,
        "temperature": temperature,
    }

    if image_base64:
        payload["image_base64"] = image_base64

    if history:
        payload["history"] = history

    if system_prompt:
        payload["system_prompt"] = system_prompt

    try:
        # stream=True é obrigatório para processar o fluxo NDJSON
        with requests.post(
            FOUNDATION_AI_CHAT_URL,
            json=payload,
            timeout=TIMEOUT_SECONDS,
            headers={"Content-Type": "application/json"},
            stream=True
        ) as r:
            if r.status_code != 200:
                yield {"type": "error", "content": f"Erro na IA: {r.status_code}"}
                return

            for line in r.iter_lines():
                if line:
                    try:
                        # Decodifica o JSON de cada linha do stream
                        event = json.loads(line.decode('utf-8'))
                        yield event
                    except json.JSONDecodeError:
                        continue

    except requests.exceptions.ConnectionError:
        yield {"type": "error", "content": "Não foi possível conectar à Foundation AI."}
    except requests.exceptions.Timeout:
        yield {"type": "error", "content": "A Foundation AI demorou demais para responder."}
    except Exception as e:
        yield {"type": "error", "content": f"Erro inesperado: {str(e)}"}

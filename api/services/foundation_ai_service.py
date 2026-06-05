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


def send_chat_request(prompt, image_base64=None, history=None, use_rag=True, temperature=0.1, system_prompt=None):
    """
    Envia uma requisição de chat para a Foundation AI local e retorna a resposta.
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
        response = requests.post(
            FOUNDATION_AI_CHAT_URL,
            json=payload,
            timeout=TIMEOUT_SECONDS,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            data = response.json()
            # Ajuste para formato síncrono esperado
            return {"success": True, "response": data.get("response", "")}

        return {
            "success": False,
            "error": response.json() if response.content else "Erro desconhecido na IA.",
            "status_code": response.status_code,
        }

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Não foi possível conectar à Foundation AI.",
            "status_code": 503,
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "A Foundation AI demorou demais para responder.",
            "status_code": 504,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro inesperado: {str(e)}",
            "status_code": 500,
        }

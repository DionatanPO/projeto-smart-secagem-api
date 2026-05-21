"""
Serviço para comunicação com a Foundation AI local.
Encaminha requisições do Django para a API de IA rodando localmente.
"""
import os
import requests

# URL completa do endpoint de chat da Foundation AI (outra API Django)
FOUNDATION_AI_CHAT_URL = os.environ.get('FOUNDATION_AI_CHAT_URL', 'http://127.0.0.1:8001/api/chat/')

TIMEOUT_SECONDS = 60


def send_chat_request(prompt, image_base64=None, history=None, use_rag=True, temperature=0.2, system_prompt=None):
    """
    Envia uma requisição de chat para a Foundation AI local e retorna a resposta.

    Args:
        prompt (str): Mensagem/pergunta do usuário. Obrigatório.
        image_base64 (str|None): Imagem em Base64 com cabeçalho (ex: data:image/jpeg;base64,...). Opcional.
        history (list|None): Histórico da conversa no formato [{"role": "user"|"assistant", "content": "..."}]. Opcional.
        use_rag (bool): Se a IA deve consultar a base interna. Padrão True.
        temperature (float): Criatividade da resposta (0.0 a 1.0). Padrão 0.2.
        system_prompt (str|None): Instrução de sistema para o comportamento da IA. Opcional.

    Returns:
        dict: {"success": True, "response": "texto da resposta"} em caso de sucesso.
              {"success": False, "error": "mensagem de erro", "status_code": int} em caso de falha.
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
            return {"success": True, "response": data.get("response", "")}

        # Erro de validação ou outro erro da API da IA
        return {
            "success": False,
            "error": response.json() if response.content else "Erro desconhecido na IA.",
            "status_code": response.status_code,
        }

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Não foi possível conectar à Foundation AI. Verifique se ela está rodando.",
            "status_code": 503,
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "A Foundation AI demorou demais para responder (timeout).",
            "status_code": 504,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro inesperado ao comunicar com a IA: {str(e)}",
            "status_code": 500,
        }

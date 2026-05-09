import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

class LocalAIService:
    def __init__(self):
        load_dotenv()
        self.base_url = os.getenv("LOCAL_AI_URL", "http://127.0.0.1:1234/v1")
        self.model = os.getenv("LOCAL_AI_MODEL", "qwen/qwen3-1.7b")
        print(f"[LocalAIService] Inicializado com URL: {self.base_url} e Modelo: {self.model}")

    def analisar_telemetria(self, silo_name, produto, dados_telemetria):
        """
        Analisa os dados de telemetria de um silo e retorna um insight usando o modelo local.
        """
        
        prompt = f"""
        Você é um especialista sênior em agronomia e conservação de grãos do sistema "Smart Secagem".
        
        CONTEXTO DO SILO:
        - Nome: {silo_name}
        - Grão Armazenado: {produto}
        
        DADOS DE TELEMETRIA (Últimas 10 coletas):
        {dados_telemetria}
        
        SUA MISSÃO:
        Analise se as condições de Temperatura e Umidade são adequadas especificamente para o grão "{produto}". 
        Considere as tabelas de equilíbrio higroscópico para este tipo de produto.
        
        FORNEÇA:
        1. Status: O grão está seguro ou em risco?
        2. Alerta: Identifique tendências de aquecimento ou excesso de umidade.
        3. Recomendação: Diga se o operador deve ligar a aeração, remover o grão ou se pode manter como está.
        
        REGRAS: Resposta curta (máximo 4 frases), tom profissional e técnico. Responda em Português.
        """
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Você é um especialista em agronomia."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=90
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.ConnectionError:
            error_msg = f"ERRO: Não foi possível conectar ao servidor local em {self.base_url}. Certifique-se de que o LM Studio ou Ollama está rodando."
            print(f"[LocalAIService] {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"Erro ao gerar análise local: {str(e)}"
            print(f"[LocalAIService] {error_msg}")
            return error_msg

    def responder_chat(self, mensagem_usuario, sistema_contexto):
        """
        Responde a uma pergunta do usuário usando o contexto completo do banco de dados.
        """
        prompt = f"""
        Você é o assistente virtual do sistema "Smart Secagem".
        Você tem acesso aos dados em tempo real do sistema abaixo:
        
        CONTEXTO DO SISTEMA:
        {sistema_contexto}
        
        PERGUNTA DO USUÁRIO:
        "{mensagem_usuario}"
        
        INSTRUÇÕES:
        - Responda de forma direta e técnica.
        - Se a pergunta for sobre dados (médias, máximas, status), use as informações do CONTEXTO acima.
        - Se não souber a resposta ou a informação não estiver no contexto, diga que não tem acesso a esse dado específico no momento.
        - Responda em Português, de forma amigável mas profissional.
        """
            
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Você é um assistente de monitoramento de silos e secagem de grãos."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3 # Menor temperatura para respostas mais precisas baseadas em fatos
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=90
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.ConnectionError:
            error_msg = f"ERRO: Servidor local offline ({self.base_url}). Inicie o servidor de IA local."
            print(f"[LocalAIService] {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"Erro na resposta do chat: {str(e)}"
            print(f"[LocalAIService] {error_msg}")
            return error_msg

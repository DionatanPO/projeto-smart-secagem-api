import google.generativeai as genai
import os
from dotenv import load_dotenv
from django.conf import settings

load_dotenv()

class GeminiService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada no arquivo .env")
        
        genai.configure(api_key=api_key.strip())
        # Usando o alias para a versão mais recente e estável (visto no list_models)
        self.model = genai.GenerativeModel('gemini-flash-latest')

    def analisar_telemetria(self, silo_name, produto, dados_telemetria):
        """
        Analisa os dados de telemetria de um silo e retorna um insight.
        dados_telemetria deve ser uma lista de dicionários com 'temperatura', 'umidade' e 'timestamp'.
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
        
        REGRAS: Resposta curta (máximo 4 frases), tom profissional e técnico.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Erro ao gerar análise: {str(e)}"

    def responder_chat(self, mensagem_usuario, contexto_silo=None):
        """
        Responde a uma pergunta genérica do usuário ou sobre um silo específico.
        """
        prompt = f"O usuário perguntou: '{mensagem_usuario}' no contexto do sistema Smart Secagem."
        if contexto_silo:
            prompt += f" Contexto do Silo: {contexto_silo}"
            
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Erro na resposta: {str(e)}"

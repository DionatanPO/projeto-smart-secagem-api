# 🌾 Smart Secagem: Monitoramento Inteligente de Grãos

![Status](https://img.shields.io/badge/Status-MVP_Funcional-brightgreen)
![Django](https://img.shields.io/badge/Backend-Django-092E20?logo=django&logoColor=white)
![Flutter](https://img.shields.io/badge/Mobile-Flutter-02569B?logo=flutter&logoColor=white)
![Python](https://img.shields.io/badge/Language-Python-3776AB?logo=python&logoColor=white)

**Plataforma oficial:** [secagemdigital.com](https://secagemdigital.com/)

A **Smart Secagem** é uma solução tecnológica completa (Web e Mobile) desenvolvida para gerenciar o processo de pós-colheita. O foco principal é a leitura e monitoramento de **sensores de temperatura e aeração** em silos e secadores, garantindo a qualidade dos grãos e evitando perdas financeiras.

## 🚀 O Ecossistema

O projeto é dividido em duas frentes integradas:

### 🌐 Painel Web (Django)
O "cérebro" da operação, responsável por:
- **Gestão de Dados:** Recebimento e processamento das leituras dos sensores via API.
- **Histórico de Sensores:** Gráficos de temperatura e umidade ao longo do tempo.
- **Controle de Aeração:** Lógica para ativação/desativação de ventiladores baseada em dados climáticos.
- **Administração de Unidades:** Cadastro de silos, tipos de grãos e lotes.

### 📱 Aplicativo Mobile (Flutter)
A ferramenta de campo do produtor rural:
- **Monitoramento Real-time:** Notificações de alerta caso a temperatura exceda o limite seguro.
- **Interface Intuitiva:** Visualização rápida do status dos sensores na palma da mão.
- **Multiplataforma:** Experiência fluida e nativa em Android e iOS.

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python / Django Framework (Django Rest Framework para API).
- **Mobile:** Flutter (Dart) com consumo de API REST.
- **Banco de Dados:** PostgreSQL (ideal para séries temporais de sensores).
- **Protocolos:** Comunicação via JSON para integração com dispositivos IoT/Sensores.

## 🎯 Funcionalidades do MVP

- **Monitoramento Térmico:** Coleta de dados de múltiplos pontos do silo.
- **Gestão de Aeração:** Monitoramento se os exaustores estão operando corretamente.
- **Alertas de Risco:** Sistema de aviso preventivo contra o aquecimento de massa de grãos.
- **Dashboard de Produção:** Visão geral da saúde dos grãos armazenados.

## 📂 Estrutura do Repositório

- `/backend-django`: Código fonte da plataforma web e API.
- `/mobile-flutter`: Projeto completo do aplicativo mobile.
- `/docs`: Documentação técnica do MVP e especificações dos sensores.

## 📦 Como Instalar (Versão Web)

1. **Clone o projeto:**
   ```bash
   git clone [https://github.com/DionatanPO/smart-secagem.git](https://github.com/DionatanPO/smart-secagem.git)

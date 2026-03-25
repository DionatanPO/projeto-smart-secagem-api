# Smart Secagem API 🌾🚀

API de alto desempenho desenvolvida em **Django REST Framework** para monitoramento inteligente de silos e sensores de secagem. O sistema gerencia o histórico de telemetria enviado por gateways externos, monitora o estado de silos e controla o acesso de usuários com diferentes níveis de permissão.

## 🛠️ Tecnologias Utilizadas

- **Python 3.x**
- **Django 6.0+**
- **Django REST Framework** (API Engine)
- **Token Authentication** (Segurança)
- **CORS Headers** (Integração com Flutter/Web)
- **SQLite** (Banco de dados padrão)

---

## 🏗️ Arquitetura do Sistema

O projeto está dividido em quatro pilares principais:

1.  **Usuários Customizados:** Login por **Username ou Email** e tipos de conta (Admin, Operador, Visualizador).
2.  **Silos:** Cadastro de unidades de armazenamento com controle de capacidade e status.
3.  **Sensores:** Configuração de hardware físico vinculado a silos específicos.
4.  **Telemetria:** Histórico contínuo de leituras (Temperatura e Umidade) vindas do campo.

---

## 🔐 Autenticação e Segurança

A API utiliza **Token Authentication**. Todas as rotas (exceto login) exigem o header:
`Authorization: Token <seu_token_aqui>`

### Obter Token (Login)
- **Endpoint:** `/api/login/`
- **Método:** `POST`
- **Campos:** `username` (ou email) e `password`.

---

## 📡 Endpoints da API

### 📉 Telemetria (Gateway IoT)
Recebe os dados brutos do equipamento de campo.
- **URL:** `/api/telemetria/`
- **Estrutura de Envio (POST):**
  ```json
  {
    "sensor_id": 10,
    "temperatura": 22.5,
    "umidade": 55.0,
    "timestamp": "2024-03-17T10:00:00Z"
  }
  ```

### 📦 Silos (Gestão de Armazenamento)
- **URL:** `/api/silos/`
- **Ações:** Listar, Criar, Editar, Deletar.
- **Campos:** `name`, `capacity`, `current_quantity`, `product_type`, `status`.

### 📟 Sensores (Configuração de Hardware)
- **URL:** `/api/sensores/`
- **Campos:** `sensor_id` (Físico), `silo` (ID do Silo), `description`, `status`.

### 👤 Usuários (Controle de Acesso)
- **URL:** `/api/usuarios/`
- **Tipos de Conta:** `admin`, `operador`, `visualizador`.

---

## 🚀 Como Executar o Projeto

1. **Ative o Ambiente Virtual:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

2. **Execute as Migrações:**
   ```powershell
   python manage.py migrate
   ```

3. **Inicie o Servidor:**
   ```powershell
   python manage.py runserver
   ```

---

## 📱 Integração com Flutter (Dicas)

- **Endereço do Emulador:** `http://10.0.2.2:8000/api/`
- **Dica de Performance:** Ao listar a telemetria, utilize filtros de data para evitar carregar milhares de registros de uma vez.
- **Logout:** Utilize a rota `/api/logout/` (POST) para invalidar o token no servidor ao sair do app.

---

## 📜 Licença
Projeto desenvolvido para o sistema **Smart Secagem**. Todos os direitos reservados.

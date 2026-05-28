# Smart Secagem — Documentação do Sistema

**Versão:** 2.0.0
**Última atualização:** Maio de 2026
**Stack:** Python 3.12 · Django 6.0 · Django REST Framework 3.16 · SQLite

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Modelo de Dados](#3-modelo-de-dados)
4. [Sistema de Níveis de Acesso](#4-sistema-de-níveis-de-acesso)
5. [API REST](#5-api-rest)
6. [Autenticação](#6-autenticação)
7. [Fluxos Operacionais](#7-fluxos-operacionais)
8. [Integração com IA](#8-integração-com-ia)
9. [Guias de Implantação](#9-guias-de-implantação)
10. [Referência Técnica](#10-referência-técnica)

---

## 1. Visão Geral

### 1.1 Propósito do Sistema

O **Smart Secagem** é um sistema de monitoramento e gestão de unidades de armazenamento e secagem de grãos. Seu objetivo principal é centralizar o controle de silos, secadores, lotes de grãos e sensores de telemetria em múltiplas fazendas, oferecendo uma API REST para integração com aplicações front-end (Flutter, Web) e gateways IoT.

### 1.2 Público-Alvo

- **Super Administradores:** Gestores de TI que administram o sistema como um todo.
- **Administradores de Fazenda:** Gerentes responsáveis por uma ou mais unidades armazenadoras.
- **Operadores:** Técnicos que executam as operações diárias de secagem e armazenagem.
- **Visualizadores:** Auditores ou consultores que necessitam apenas de acesso de leitura.
- **Gateways IoT:** Dispositivos de campo que enviam leituras de sensores automaticamente.

### 1.3 Funcionalidades Principais

| Funcionalidade | Descrição |
|---|---|
| Gestão de Usuários | Cadastro hierárquico com 4 níveis de acesso |
| Gestão de Fazendas | Cadastro e gerenciamento de unidades armazenadoras |
| Controle de Silos | Capacidade, status e ocupação |
| Controle de Lotes de Grãos | Entrada, processamento e despacho |
| Gestão de Secadores | Tipos, capacidade e fonte de calor |
| Processos Operacionais | Secagem, resfriamento e armazenamento |
| Sensores IoT | Cadastro de dispositivos físicos |
| Telemetria | Leituras contínuas de temperatura e umidade |
| Cadastro de Clientes | Produtores vinculados a fazendas |
| Assistente IA | Chat contextual com IA local |
| Painel Administrativo | Interface web do Django Admin |

---

## 2. Arquitetura do Sistema

### 2.1 Visão de Alto Nível

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SMART SECAGEM                                 │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                   Django 6.0 / DRF 3.16                      │    │
│  │                                                              │    │
│  │  ┌──────────────────┐    ┌──────────────────────────────┐   │    │
│  │  │   api (REST API) │    │  plataforma (Web Legacy)     │   │    │
│  │  │                  │    │                              │   │    │
│  │  │  /api/sensores/  │    │  /dashboard/                 │   │    │
│  │  │  /api/silos/     │    │  /silos/                     │   │    │
│  │  │  /api/lotes/     │    │  /sensores/                  │   │    │
│  │  │  /api/processos/ │    │  /controladores/             │   │    │
│  │  │  /api/fazendas/  │    │  /alertas/                   │   │    │
│  │  │  /api/usuarios/  │    │  /api/ (Views antigas)      │   │    │
│  │  │  /api/telemetria/│    │                              │   │    │
│  │  │  /api/chat/      │    └──────────────────────────────┘   │    │
│  │  └──────────────────┘                                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                │                                     │
│                    ┌───────────┴───────────┐                         │
│                    │     SQLite / SQL      │                         │
│                    │     db.sqlite3        │                         │
│                    └───────────────────────┘                         │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │           Integrações                                         │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │    │
│  │  │  Flutter App  │  │  Gateway IoT │  │ Foundation AI    │   │    │
│  │  │  (Mobile)     │  │  (ESP32,etc) │  │ (Local LLM)      │   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Stack Tecnológica

| Componente | Tecnologia | Versão |
|---|---|---|
| Linguagem | Python | 3.12 |
| Framework Web | Django | 6.0.3 |
| API Framework | Django REST Framework | 3.16.1 |
| Banco de Dados | SQLite | 3.x |
| Autenticação API | Token Authentication (DRF) | — |
| CORS | django-cors-headers | 4.9.0 |
| Fuso Horário | America/Sao_Paulo (UTC−3) | — |
| Timezone ativo | `USE_TZ = False` | — |

### 2.3 Apps do Projeto

| App | Função |
|---|---|
| `api` | REST API principal com todos os modelos de negócio |
| `plataforma` | Interface web legada (AdminLTE + Django views) |
| `core` | Configurações globais do projeto |

---

## 3. Modelo de Dados

### 3.1 Diagrama de Entidades e Relacionamentos

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              USER (Usuário)                                 │
│  id │ username │ email │ password │ account_type │ telefone │ farm (FK)    │
└────────┬──────────────────────────────────────────────────────────┬────────┘
         │ 1                                                    N  │
         │ owner (FK)                                              │ operadores (related_name)
         ▼                                                         ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                              FARM (Fazenda)                                 │
│  id │ owner (FK) │ name │ location │ description │ created_at               │
└──┬───────────────┬───────────────┬──────────────┬──────────────┬───────────┘
   │ 1          N │ 1          N │ 1          N │ 1          N │ 1          N
   │ silos       │ lotes        │ secadores    │ clientes     │ sensors
   ▼             ▼               ▼              ▼              ▼
┌─────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────────┐
│ SILO    │ │ LOTE     │ │ SECADOR   │ │ CLIENTE  │ │ SENSORDATA   │
│─────────│ │──────────│ │───────────│ │──────────│ │──────────────│
│ name    │ │ num_lote │ │ nome      │ │ nome     │ │ sensor_id    │
│ capacity│ │ cultura  │ │ tipo      │ │ email    │ │ tipo         │
│ qty     │ │ safra    │ │ cap(t/h)  │ │ tel      │ │ farm (FK)    │
│ status  │ │ peso_in  │ │ calor     │ │ cpf_cnpj │ │ silo (FK)    │
│ farm(FK)│ │ umid_in  │ │ status    │ │ farm(FK) │ │ secador (FK) │
└─────────┘ │ peso_fim │ │ farm(FK)  │ └──────────┘ │ description  │
            │ silo(FK) │ └───────────┘              │ status       │
            │ cliente  │      1                  N  └──────┬───────┘
            │ status   │      │ processo(FK)               │ 1
            │ farm(FK) │      ▼                            │ sensor (FK)
            └─────┬────┘ ┌──────────┐                      ▼
                  │    N  │ PROCESSO │              ┌─────────────┐
                  └──────│──────────│              │  TELEMETRY  │
                         │ tipo     │              │─────────────│
                         │ lote(FK) │              │ temperatura │
                         │ secador  │              │ umidade     │
                         │ silo(FK) │              │ timestamp   │
                         │ status   │              │ extras(JSON)│
                         │ operador │              └─────────────┘
                         │ inicio   │
                         └──────────┘
```

### 3.2 Entidades Detalhadas

#### 3.2.1 User (`api/models.py`)

Modelo de usuário customizado que estende `AbstractUser`.

| Campo | Tipo | Descrição |
|---|---|---|
| `username` | CharField | Nome de usuário único |
| `email` | EmailField | E-mail do usuário |
| `password` | CharField | Senha (hashed) |
| `account_type` | CharField | `super_admin`, `admin`, `operador`, `visualizador` |
| `telefone` | CharField | Telefone de contato |
| `farm` | ForeignKey → Farm | Vínculo do operador a uma fazenda |
| `is_staff` | Boolean | Acesso ao painel admin (automático) |
| `is_superuser` | Boolean | Super privilégios (só super_admin) |

**Métodos de negócio:**

- `get_accessible_farms()` — Retorna as fazendas que o usuário pode acessar conforme seu nível hierárquico.
- `can_manage_type(target_type)` — Verifica se o usuário pode gerenciar usuários de um tipo inferior.
- `can_manage_user(target_user)` — Verifica se o usuário pode gerenciar outro usuário específico.

**Regras automáticas no `save()`:**

| `account_type` | `is_staff` | `is_superuser` |
|---|---|---|
| `super_admin` | `True` | `True` |
| `admin` | `True` | `False` |
| `operador` | `True` | `False` |
| `visualizador` | `False` | `False` |

#### 3.2.2 Farm (`api/models.py`)

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | AutoField | Identificador único |
| `owner` | ForeignKey → User | Administrador dono da fazenda |
| `name` | CharField(100) | Nome da fazenda/armazém |
| `location` | CharField(200) | Cidade/localização |
| `description` | TextField | Observações |
| `created_at` | DateTimeField | Data de criação |

#### 3.2.3 Silo (`api/models.py`)

| Campo | Tipo | Descrição |
|---|---|---|
| `name` | CharField | Nome do silo |
| `farm` | ForeignKey → Farm | Fazenda vinculada |
| `capacity` | FloatField | Capacidade máxima (toneladas) |
| `current_quantity` | FloatField | Quantidade atual (toneladas) |
| `status` | CharField | `disponivel`, `em_uso`, `manutencao`, `desativado` |
| `observations` | TextField | Observações |
| `created_at` | DateTimeField | Data de criação |
| `updated_at` | DateTimeField | Data da última atualização |

#### 3.2.4 Lote (`api/models.py`)

| Campo | Tipo | Descrição |
|---|---|---|
| `numero_lote` | CharField | Código único gerado automaticamente (LOTE-XXXX) |
| `farm` | ForeignKey → Farm | Fazenda de origem |
| `cliente` | ForeignKey → Cliente | Produtor/cliente dono do lote |
| `cultura` | CharField | Tipo de grão (Milho, Soja...) |
| `variedade` | CharField | Variedade da cultura |
| `safra` | CharField | Ano/safra |
| `peso_inicial` | FloatField | Peso na entrada (kg) |
| `umidade_inicial` | FloatField | Umidade na entrada (%) |
| `data_entrada` | DateTimeField | Data de entrada (automática) |
| `peso_final` | FloatField | Peso na saída (kg) |
| `umidade_final` | FloatField | Umidade na saída (%) |
| `data_saida` | DateTimeField | Data de saída |
| `silo` | ForeignKey → Silo | Silo de destino |
| `status` | CharField | Vide seção de fluxos |
| `observacoes` | TextField | Observações |

**Automações no `save()`:**
- Gera automaticamente o `numero_lote` no formato `LOTE-XXXX`.
- Sincroniza o status do silo: `'despachado'` libera o silo (`disponivel`), demais status marcam como `em_uso`.

#### 3.2.5 Secador (`api/models.py`)

| Campo | Tipo | Descrição |
|---|---|---|
| `nome` | CharField | Nome do secador |
| `farm` | ForeignKey → Farm | Fazenda vinculada |
| `tipo` | CharField | `Coluna`, `Cascata`, `Fluxo Contínuo`, `Batelada` |
| `capacidade` | FloatField | Capacidade em toneladas/hora |
| `fonte_calor` | CharField | `Lenha`, `Gás GLP`, `Biomassa`, `Elétrico` |
| `status` | CharField | `Disponível`, `Em Uso`, `Em Manutenção`, `Desativado` |
| `observacoes` | TextField | Observações |

#### 3.2.6 Processo (`api/models.py`)

| Campo | Tipo | Descrição |
|---|---|---|
| `tipo_processo` | CharField | `Secagem`, `Resfriamento`, `Armazenamento` |
| `lote` | ForeignKey → Lote | Lote sendo processado |
| `secador` | ForeignKey → Secador | Secador utilizado |
| `silo` | ForeignKey → Silo | Silo utilizado |
| `data_inicio` | DateTimeField | Início do processo |
| `data_fim` | DateTimeField | Fim do processo |
| `status` | CharField | `Iniciada`, `Pausada`, `Finalizada`, `Cancelada` |
| `responsavel` | ForeignKey → User | Operador responsável |

**Regras de negócio no `save()`:**
- **Impede duplicidade de atividade:** Um lote não pode ter dois processos ativos simultaneamente.
- **Sincroniza status do lote:** Atualiza automaticamente o status do lote para `"{tipo_processo} ({status})"`.

#### 3.2.7 SensorData (`api/models.py`)

Configuração de sensores físicos.

| Campo | Tipo | Descrição |
|---|---|---|
| `sensor_id` | CharField(50) | ID físico do sensor (ex: `SENSOR_01`) — único |
| `tipo` | CharField | Tipo de dispositivo |
| `silo` | ForeignKey → Silo | Silo ao qual está vinculado |
| `secador` | ForeignKey → Secador | Secador ao qual está vinculado |
| `farm` | ForeignKey → Farm | Farm direta (fallback) |
| `description` | CharField | Descrição/localização |
| `status` | CharField | `ativo`, `manutencao`, `falha`, `desativado` |

#### 3.2.8 Telemetry (`api/models.py`)

Leituras enviadas pelos sensores.

| Campo | Tipo | Descrição |
|---|---|---|
| `sensor` | ForeignKey → SensorData | Sensor que gerou a leitura |
| `temperatura` | FloatField | Temperatura em °C |
| `umidade` | FloatField | Umidade em % |
| `dados_extras` | JSONField | Metadados adicionais |
| `timestamp` | DateTimeField | Data/hora da coleta (enviado pelo gateway) |
| `received_at` | DateTimeField | Data/hora de recebimento (automático) |

#### 3.2.9 Cliente (`api/models.py`)

| Campo | Tipo | Descrição |
|---|---|---|
| `farm` | ForeignKey → Farm | Fazenda vinculada (obrigatório) |
| `nome` | CharField | Nome completo |
| `email` | EmailField | E-mail |
| `telefone` | CharField | Telefone |
| `cpf_cnpj` | CharField(20) | CPF ou CNPJ (único) |
| `endereco` | TextField | Endereço completo |
| `created_at` | DateTimeField | Data de criação |
| `updated_at` | DateTimeField | Data da última atualização |

---

## 4. Sistema de Níveis de Acesso

### 4.1 Hierarquia de Perfis

O sistema implementa 4 níveis hierárquicos de acesso, onde cada nível pode gerenciar os níveis abaixo dele:

```
Nível 0 — super_admin (Super Administrador)
    │  Pode criar, ver e gerenciar todos os perfis abaixo
    │
Nível 1 — admin (Administrador)
    │  Pode criar, ver e gerenciar operadores e visualizadores
    │  (apenas dentro de suas próprias fazendas)
    │
Nível 2 — operador (Operador)
    │  Não pode gerenciar usuários
    │
Nível 3 — visualizador (Visualizador)
    │  Acesso somente leitura
```

### 4.2 Matriz de Permissões

#### Legenda
| Símbolo | Significado |
|---|---|
| ✅ | Permitido |
| ❌ | Bloqueado |
| — | Não se aplica |

#### Operações por Tipo de Dado

| Ação | super_admin | admin | operador | visualizador |
|---|---|---|---|---|
| **Fazendas** | | | | |
| Listar | ✅ (todas) | ✅ (suas) | ✅ (vinculada) | ✅ (conforme farm) |
| Criar | ✅ | ✅ | ❌ | ❌ |
| Editar | ✅ | ✅ | ❌ | ❌ |
| Excluir | ✅ | ✅ | ❌ | ❌ |
| **Silos** | | | | |
| Listar | ✅ (todos) | ✅ (seus) | ✅ (sua farm) | ✅ (sua farm) |
| Criar | ✅ | ✅ | ✅ | ❌ |
| Editar | ✅ | ✅ | ✅ | ❌ |
| Excluir | ✅ | ✅ | ❌ | ❌ |
| **Lotes** | | | | |
| Listar | ✅ (todos) | ✅ (seus) | ✅ (sua farm) | ✅ (sua farm) |
| Criar | ✅ | ✅ | ✅ | ❌ |
| Editar | ✅ | ✅ | ✅ | ❌ |
| Excluir | ✅ | ✅ | ❌ | ❌ |
| **Secadores** | | | | |
| Listar | ✅ (todos) | ✅ (seus) | ✅ (sua farm) | ✅ (sua farm) |
| Criar | ✅ | ✅ | ✅ | ❌ |
| Editar | ✅ | ✅ | ✅ | ❌ |
| Excluir | ✅ | ✅ | ❌ | ❌ |
| **Processos** | | | | |
| Listar | ✅ (todos) | ✅ (seus) | ✅ (sua farm) | ✅ (sua farm) |
| Criar | ✅ | ✅ | ✅ | ❌ |
| Editar | ✅ | ✅ | ✅ | ❌ |
| Excluir | ✅ | ✅ | ❌ | ❌ |
| **Sensores** | | | | |
| Listar | ✅ (todos) | ✅ (seus) | ✅ (sua farm) | ✅ (sua farm) |
| Criar | ✅ | ✅ | ✅ | ❌ |
| Editar | ✅ | ✅ | ✅ | ❌ |
| Excluir | ✅ | ✅ | ❌ | ❌ |
| **Clientes** | | | | |
| Listar | ✅ (todos) | ✅ (seus) | ✅ (sua farm) | ✅ (sua farm) |
| Criar | ✅ | ✅ | ✅ | ❌ |
| Editar | ✅ | ✅ | ✅ | ❌ |
| Excluir | ✅ | ✅ | ❌ | ❌ |
| **Telemetria** | | | | |
| Listar | ✅ (todos) | ✅ (seus) | ✅ (sua farm) | ✅ (sua farm) |
| Criar | ✅ | ✅ | ✅ | ❌ |
| Editar | ✅ | ✅ | ✅ | ❌ |
| Excluir | ✅ | ✅ | ❌ | ❌ |
| **Usuários** | | | | |
| Listar | ✅ (todos) | ✅ (sua farm) | ❌ | ❌ |
| Criar | ✅ (todos) | ✅ (oper/vis apenas) | ❌ | ❌ |
| Editar | ✅ (todos) | ✅ (oper/vis apenas) | ❌ | ❌ |
| Excluir | ✅ (todos) | ✅ (oper/vis apenas) | ❌ | ❌ |

### 4.3 Visibilidade de Dados por Farm

O método `get_accessible_farms()` define o escopo de dados que cada usuário enxerga:

```python
def get_accessible_farms(self):
    if self.account_type == 'super_admin':
        return Farm.objects.all()                                  # Todas as fazendas
    if self.account_type == 'operador' and self.farm:
        return Farm.objects.filter(id=self.farm.id)                # Apenas sua fazenda
    if self.account_type == 'admin':
        return self.farms.all()                                    # Suas fazendas (owner)
    return Farm.objects.none()                                     # Nenhuma
```

### 4.4 Mecanismo de Permissões (Código)

O sistema utiliza 3 classes de permissão no arquivo `api/permissions.py`:

#### `IsAdminOrReadOnly`
- **Aplica-se a:** `FarmViewSet`
- **Efeito:** `super_admin` e `admin` podem tudo; operador e visualizador apenas leitura (GET, HEAD, OPTIONS)

#### `IsAdminOrDeleteOnly`
- **Aplica-se a:** `LoteViewSet`, `ClienteViewSet`, `SecadorViewSet`, `ProcessoViewSet`, `SensorDataViewSet`
- **Efeito:** `super_admin` e `admin` podem tudo; operador pode criar/editar mas **não excluir**; visualizador apenas leitura

#### `CanManageUsers`
- **Aplica-se a:** `UserViewSet`
- **Efeito:** `super_admin` e `admin` acessam o endpoint de usuários; operador e visualizador são barrados (devem usar `/api/me/`)
- Possui `has_object_permission` para validar que:
  - Admin só gerencia usuários de tipo inferior
  - Usuário pode editar o próprio perfil via PATCH

### 4.5 Hierarquia no Modelo (Código)

```python
HIERARCHY = {
    'super_admin': 0,
    'admin':        1,
    'operador':     2,
    'visualizador': 3,
}

def can_manage_type(self, target_type):
    my_level = self.HIERARCHY.get(self.account_type, 99)
    target_level = self.HIERARCHY.get(target_type, 99)
    return my_level < target_level
```

### 4.6 UserViewSet — Filtragem por Hierarquia

```python
def get_queryset(self):
    user = self.request.user
    if user.account_type == 'super_admin':
        return User.objects.all()                                           # Vê todos
    if user.account_type == 'admin':
        my_farms = user.farms.all()
        return User.objects.filter(                                         # Vê apenas oper/vis de suas farms
            farm__in=my_farms, account_type__in=['operador', 'visualizador']
        ) | User.objects.filter(id=user.id)                                 # + ele mesmo
    return User.objects.none()
```

---

## 5. API REST

### 5.1 Endpoints

| Método | Endpoint | Descrição | Permissão |
|---|---|---|---|
| **Autenticação** | | | |
| POST | `/api/login/` | Obter token de autenticação | Pública |
| POST | `/api/logout/` | Invalidar token | Autenticado |
| GET/PATCH | `/api/me/` | Dados do próprio usuário | Autenticado |
| POST | `/api/chat/` | Assistente IA | Autenticado |
| **Fazendas** | | | |
| GET | `/api/fazendas/` | Listar fazendas | Autenticado |
| POST | `/api/fazendas/` | Criar fazenda | super_admin, admin |
| GET | `/api/fazendas/{id}/` | Detalhe da fazenda | Autenticado |
| PUT/PATCH | `/api/fazendas/{id}/` | Atualizar fazenda | super_admin, admin |
| DELETE | `/api/fazendas/{id}/` | Excluir fazenda | super_admin, admin |
| **Silos** | | | |
| GET | `/api/silos/` | Listar silos | Autenticado |
| POST | `/api/silos/` | Criar silo | super_admin, admin, operador |
| GET | `/api/silos/{id}/` | Detalhe do silo | Autenticado |
| PUT/PATCH | `/api/silos/{id}/` | Atualizar silo | super_admin, admin, operador |
| DELETE | `/api/silos/{id}/` | Excluir silo | super_admin, admin |
| **Lotes** | | | |
| GET | `/api/lotes/` | Listar lotes | Autenticado |
| POST | `/api/lotes/` | Criar lote | super_admin, admin, operador |
| GET | `/api/lotes/{id}/` | Detalhe do lote | Autenticado |
| PUT/PATCH | `/api/lotes/{id}/` | Atualizar lote | super_admin, admin, operador |
| DELETE | `/api/lotes/{id}/` | Excluir lote | super_admin, admin |
| **Secadores** | | | |
| GET | `/api/secadores/` | Listar secadores | Autenticado |
| POST | `/api/secadores/` | Criar secador | super_admin, admin, operador |
| GET | `/api/secadores/{id}/` | Detalhe do secador | Autenticado |
| PUT/PATCH | `/api/secadores/{id}/` | Atualizar secador | super_admin, admin, operador |
| DELETE | `/api/secadores/{id}/` | Excluir secador | super_admin, admin |
| **Processos** | | | |
| GET | `/api/processos/` | Listar processos | Autenticado |
| POST | `/api/processos/` | Criar processo | super_admin, admin, operador |
| GET | `/api/processos/{id}/` | Detalhe do processo | Autenticado |
| PUT/PATCH | `/api/processos/{id}/` | Atualizar processo | super_admin, admin, operador |
| DELETE | `/api/processos/{id}/` | Excluir processo | super_admin, admin |
| **Sensores** | | | |
| GET | `/api/sensores/` | Listar sensores | Autenticado |
| POST | `/api/sensores/` | Criar sensor | super_admin, admin, operador |
| GET | `/api/sensores/{id}/` | Detalhe do sensor | Autenticado |
| PUT/PATCH | `/api/sensores/{id}/` | Atualizar sensor | super_admin, admin, operador |
| DELETE | `/api/sensores/{id}/` | Excluir sensor | super_admin, admin |
| **Telemetria** | | | |
| GET | `/api/telemetria/` | Listar telemetria | Autenticado |
| POST | `/api/telemetria/` | Criar leitura | Autenticado |
| GET | `/api/telemetria/{id}/` | Detalhe da leitura | Autenticado |
| **Clientes** | | | |
| GET | `/api/clientes/` | Listar clientes | Autenticado |
| POST | `/api/clientes/` | Criar cliente | super_admin, admin, operador |
| GET | `/api/clientes/{id}/` | Detalhe do cliente | Autenticado |
| PUT/PATCH | `/api/clientes/{id}/` | Atualizar cliente | super_admin, admin, operador |
| DELETE | `/api/clientes/{id}/` | Excluir cliente | super_admin, admin |
| **Usuários** | | | |
| GET | `/api/usuarios/` | Listar usuários | super_admin, admin |
| POST | `/api/usuarios/` | Criar usuário | super_admin, admin |
| GET | `/api/usuarios/{id}/` | Detalhe do usuário | super_admin, admin |
| PUT/PATCH | `/api/usuarios/{id}/` | Atualizar usuário | super_admin, admin |
| DELETE | `/api/usuarios/{id}/` | Excluir usuário | super_admin, admin |

### 5.2 Filtros Disponíveis

#### Telemetria (`GET /api/telemetria/`)
| Parâmetro | Exemplo | Descrição |
|---|---|---|
| `sensor` | `3` | Filtrar pelo ID do sensor no banco |
| `silo` | `1` | Filtrar por silo (todos sensores do silo) |
| `silo_id` | `1` | Alternativo para silo |
| `sensor_id` | `SENSOR_01` | Filtrar pelo ID físico do sensor |
| `data` | `2026-05-28` | Filtrar por data específica |

#### Sensores (`GET /api/sensores/`)
| Parâmetro | Exemplo | Descrição |
|---|---|---|
| `silo` | `1` | Filtrar sensores de um silo específico |
| `silo_id` | `1` | Alternativo para silo |

### 5.3 Exemplos de Requisição e Resposta

#### Criar Fazenda
```
POST /api/fazendas/
Authorization: Token abc123...

Request:
{
  "name": "Fazenda Boa Vista",
  "location": "Campo Grande, MS",
  "description": "Unidade de armazenagem principal"
}

Response (201):
{
  "id": 1,
  "name": "Fazenda Boa Vista",
  "location": "Campo Grande, MS",
  "description": "Unidade de armazenagem principal",
  "owner": 2,
  "created_at": "2026-05-28T10:00:00"
}
```

#### Criar Operador
```
POST /api/usuarios/
Authorization: Token abc123...

Request:
{
  "username": "joao.operador",
  "email": "joao@email.com",
  "password": "senha123",
  "account_type": "operador",
  "first_name": "João",
  "last_name": "Silva",
  "telefone": "(67) 99999-8888",
  "farm": 1
}

Response (201):
{
  "id": 5,
  "username": "joao.operador",
  "email": "joao@email.com",
  "account_type": "operador",
  "is_staff": true,
  "first_name": "João",
  "last_name": "Silva",
  "telefone": "(67) 99999-8888",
  "farm": 1
}
```

#### Enviar Telemetria (Gateway IoT)
```
POST /api/telemetria/
Content-Type: application/json

Request:
{
  "sensor_id": "SENSOR_01",
  "temperatura": 28.5,
  "umidade": 65.0,
  "timestamp": "2026-05-28T14:30:00Z"
}

Response (201):
{
  "id": 1024,
  "sensor": 3,
  "sensor_physical_id": "SENSOR_01",
  "temperatura": 28.5,
  "umidade": 65.0,
  "timestamp": "2026-05-28T14:30:00Z",
  "received_at": "2026-05-28T14:30:05.123456"
}
```

> **Nota sobre a telemetria:** O parâmetro `sensor_id` aceita tanto o ID numérico do banco quanto o **ID físico** string do sensor. Se for uma string, o sistema faz a resolução automática para o ID correto.

#### Chat com IA
```
POST /api/chat/
Authorization: Token abc123...

Request:
{
  "prompt": "Qual a temperatura atual do silo 1?",
  "history": [],
  "use_rag": true,
  "temperature": 0.1
}

Response (200):
{
  "response": "No silo 'Silo Principal' da 'Fazenda Boa Vista' a temperatura atual é 28.5°C, registrada às 14:30 do dia 28/05/2026."
}
```

### 5.4 Autenticação

#### Obter Token
```
POST /api/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response (200):
{
  "token": "a1b2c3d4e5f6..."
}
```

#### Usar Token
```
Authorization: Token a1b2c3d4e5f6...
```

#### Logout
```
POST /api/logout/
Authorization: Token a1b2c3d4e5f6...

Response (200):
{
  "message": "Logout realizado com sucesso"
}
```

> **Login por Email:** O backend `EmailOrUsernameModelBackend` permite autenticação tanto por `username` quanto por `email` indistintamente.

#### Endpoint `/api/me/`
Disponível para qualquer usuário autenticado. Retorna os dados do próprio perfil e permite atualizações parciais via PATCH.

```
GET /api/me/
Authorization: Token a1b2c3d4e5f6...

Response (200):
{
  "id": 2,
  "username": "dionatan",
  "email": "dionatan@email.com",
  "first_name": "Dionatan",
  "last_name": "",
  "telefone": null,
  "account_type": "admin"
}
```

---

## 6. Fluxos Operacionais

### 6.1 Ciclo de Vida de um Lote

```
                    ┌──────────────┐
                    │  AGUARDANDO  │
                    └──────┬───────┘
                           │
               ┌───────────┴───────────┐
               ▼                       ▼
      ┌────────────────┐      ┌────────────────┐
      │ Secagem        │      │ Aeração         │
      │ (Iniciada)     │      │ (Iniciada)      │
      ├────────────────┤      ├────────────────┤
      │ (Pausada)      │      │ (Pausada)       │
      ├────────────────┤      ├────────────────┤
      │ (Finalizada)   │      │ (Finalizada)    │
      │ (Cancelada)    │      │ (Cancelada)     │
      └────────┬───────┘      └────────┬────────┘
               │                       │
               └───────────┬───────────┘
                           ▼
                    ┌──────────────┐
                    │  FINALIZADO  │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  DESPACHADO  │ → Silo liberado
                    └──────────────┘
```

### 6.2 Criação de Usuário (Fluxo Hierárquico)

```
SUPER_ADMIN                     ADMIN
     │                            │
     │  POST /api/usuarios/       │  POST /api/usuarios/
     │  {account_type: "admin"}   │  {account_type: "operador",
     │                            │   farm: 1}
     ▼                            ▼
┌──────────────────┐     ┌──────────────────┐
│ can_manage_type  │     │ can_manage_type  │
│ ("admin")        │     │ ("operador")     │
│ super_admin(0)   │     │ admin(1) <       │
│ < admin(1) → ✅  │     │ operador(2) → ✅ │
└──────────────────┘     └──────────────────┘
     │                            │
     ▼                            ▼
  Admin criado               Operador criado
  (is_staff=True,            (vinculado à farm
   is_superuser=False)        do admin)
```

### 6.3 Regra de Negócio: Conflito de Processos

Um lote **não pode** ter dois processos (secagem, resfriamento, armazenamento) ativos simultaneamente.

```python
conflito = Processo.objects.filter(
    lote=self.lote,
    status__in=['Iniciada', 'Pausada']
).exclude(pk=self.pk).exists()

if conflito:
    raise ValueError(
        f"O lote {self.lote.numero_lote} já possui uma "
        f"atividade em andamento ou pausada."
    )
```

### 6.4 Regra de Negócio: Validação de Lote

Ao criar ou editar um lote, o sistema valida:

1. **Capacidade do silo:** O `peso_inicial` não pode exceder a capacidade do silo (em kg).
2. **Ocupação do silo:** Não pode haver outro lote ativo (`aguardando` ou `secando`) no mesmo silo.

---

## 7. Integração com IA

### 7.1 Assistente Inteligente

O sistema possui um endpoint `/api/chat/` que encaminha perguntas para uma **Foundation AI** local (outra API Django rodando em paralelo).

**Fluxo:**

```
Usuário → Smart Secagem → Foundation AI → LLM Local → Resposta
              │
              ├── Coleta contexto do banco
              │   (farms, silos, lotes, sensores, telemetria)
              │
              └── Enriquece o prompt com dados em tempo real
```

**Configuração:**

| Variável | Default | Descrição |
|---|---|---|
| `FOUNDATION_AI_CHAT_URL` | `http://127.0.0.1:8001/api/chat/` | URL da IA |
| `TIMEOUT_SECONDS` | 60 | Timeout em segundos |

**Contexto enviado para a IA:**

O sistema coleta automaticamente os dados do banco (escopo da fazenda do usuário) e anexa ao prompt como contexto, incluindo:
- Dados das fazendas
- Silos com capacidade e status
- Lotes com culturas, pesos e umidades
- Secadores com tipos e status
- Processos ativos
- Sensores e últimas telemetrias

---

## 8. Guias de Implantação

### 8.1 Requisitos

- Python 3.12 ou superior
- Pip (gerenciador de pacotes)
- (Opcional) Foundation AI para funcionalidade de chat

### 8.2 Setup do Ambiente

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd Projeto-SMART-SECAGEM-API

# 2. Criar e ativar ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate    # Linux/macOS

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar migrações
python manage.py migrate

# 5. Criar super admin
python manage.py createsuperuser  # account_type será 'super_admin' pelo admin

# 6. Iniciar servidor
python manage.py runserver
```

### 8.3 Criar Primeiro Super Administrador

```bash
python manage.py shell -c "
from api.models import User
u = User.objects.create_superuser(
    username='admin',
    email='admin@email.com',
    password='admin123'
)
u.account_type = 'super_admin'
u.save()
"
```

### 8.4 Configuração de Produção

Para ambiente de produção, recomenda-se:

1. **Banco de dados:** Migrar para PostgreSQL ou MySQL
2. **Secret Key:** Alterar `SECRET_KEY` no `settings.py`
3. **Debug:** Definir `DEBUG = False`
4. **Allowed Hosts:** Configurar `ALLOWED_HOSTS` com os domínios permitidos
5. **HTTPS:** Utilizar proxy reverso (Nginx) com SSL
6. **Autenticação:** Considerar JWT em vez de Token para maior escalabilidade

### 8.5 Migrações

```bash
# Criar migrações após alterações nos modelos
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Verificar SQL gerado
python manage.py sqlmigrate api 0035
```

---

## 9. Guia de Estilo e Boas Práticas

### 9.1 Convenções de Código

- **Python:** Seguir PEP 8
- **Nomenclatura de modelos:** PascalCase (ex: `SensorData`, `AeracaoSilo`)
- **Nomenclatura de campos:** snake_case (ex: `numero_lote`, `data_entrada`)
- **Nomenclatura de views/viewsets:** PascalCase com sufixo ViewSet (ex: `LoteViewSet`)
- **Nomenclatura de endpoints:** plural e em português (ex: `/api/sensores/`, `/api/fazendas/`)
- **Serializers:** Mesmo nome do modelo + "Serializer" (ex: `LoteSerializer`)

### 9.2 Estrutura de Commits

Recomenda-se o padrão [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: adiciona campo farm ao modelo Cliente
fix: corrige permissão de exclusão para operadores
docs: atualiza documentação da API
refactor: simplifica lógica de get_accessible_farms
```

---

## 10. Referência Técnica

### 10.1 Arquivos do Projeto

```
Projeto-SMART-SECAGEM-API/
│
├── api/                           # App principal — REST API
│   ├── __init__.py
│   ├── admin.py                   # Configuração do Django Admin
│   ├── apps.py                    # Configuração do app
│   ├── backends.py                # Backend de autenticação (email/username)
│   ├── models.py                  # Todos os modelos de dados
│   ├── permissions.py             # Classes de permissão customizadas
│   ├── serializers.py             # Serializers DRF
│   ├── urls.py                    # Rotas da API
│   ├── views.py                   # ViewSets e views da API
│   ├── tests.py                   # Testes unitários
│   ├── migrations/                # Migrações do banco de dados
│   │   ├── 0001_initial.py
│   │   ├── ...
│   │   └── 0035_cliente_farm_alter_user_account_type.py
│   └── services/
│       ├── __init__.py
│       ├── foundation_ai_service.py   # Comunicação com IA local
│       └── context_service.py         # Coleta de contexto para IA
│
├── plataforma/                    # App legado — interface web
│   ├── __init__.py
│   ├── admin.py
│   ├── api/                       # ViewSets antigos
│   │   ├── serializers.py
│   │   └── viewsets.py
│   ├── apps.py
│   ├── backends.py
│   ├── consumers.py               # WebSockets (notificações)
│   ├── forms.py                   # Formulários Django
│   ├── models.py                  # Modelos legados
│   ├── routing.py                 # Rotas de WebSocket
│   ├── signals.py                 # Signals Django
│   ├── templates/                 # Templates HTML (AdminLTE)
│   ├── templatetags/              # Template tags customizadas
│   ├── urls.py                    # Rotas web
│   ├── utils.py                   # Utilitários do admin
│   └── views.py                   # Views baseadas em função
│
├── core/                          # Configurações do projeto
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py                # Configurações Django
│   ├── urls.py                    # Rotas raiz
│   └── wsgi.py
│
├── venv/                          # Ambiente virtual
├── manage.py                      # CLI do Django
├── requirements.txt               # Dependências do projeto
├── DOCUMENTACAO.md                # Este documento
└── README.md                      # README do projeto
```

### 10.2 Dependências (`requirements.txt`)

```
asgiref==3.11.1
Django==6.0.3
django-cors-headers==4.9.0
djangorestframework==3.16.1
sqlparse==0.5.5
tzdata==2025.3
```

### 10.3 Configurações do Django (`core/settings.py`)

| Configuração | Valor |
|---|---|
| `AUTH_USER_MODEL` | `api.User` |
| `AUTHENTICATION_BACKENDS` | `api.backends.EmailOrUsernameModelBackend` |
| `LANGUAGE_CODE` | `pt-br` |
| `TIME_ZONE` | `America/Sao_Paulo` |
| `USE_TZ` | `False` |
| `CORS_ALLOW_ALL_ORIGINS` | `True` |
| `REST_FRAMEWORK.DEFAULT_AUTHENTICATION` | `TokenAuthentication`, `SessionAuthentication` |

---

## Histórico de Versões

| Versão | Data | Principais Alterações |
|---|---|---|
| 1.0.0 | — | Versão inicial do sistema |
| 2.0.0 | Mai/2026 | Hierarquia de 4 níveis (`super_admin`, `admin`, `operador`, `visualizador`); vínculo Cliente → Farm; permissões refinadas com `IsAdminOrReadOnly`, `IsAdminOrDeleteOnly` e `CanManageUsers`; escopagem de dados por farm |

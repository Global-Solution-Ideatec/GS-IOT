# README.md Completo - IdeiaTech SmartLeader

Aqui está o README.md completo e profissional em formato markdown:

```markdown
<div align="center">

# 🚀 IdeiaTech - SmartLeader API

### Sistema de Gestão Inteligente de Trabalho Híbrido com IA Generativa

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com)
[![License](https://img.shields.io/badge/License-FIAP_GS_2025-yellow.svg?style=flat)](LICENSE)

[Sobre](#sobre) • [Instalação](#instalação) • [Uso](#uso) • [API](#api)

</div>

---

## 📋 Sobre o Projeto

O **SmartLeader** é uma plataforma inovadora desenvolvida pela **IdeiaTech** que utiliza **Inteligência Artificial Generativa** (Google Gemini) para revolucionar a gestão de equipes em ambientes de trabalho híbrido.

### 🎯 Problema que Resolve

- ⚖️ Falta de equilíbrio entre produtividade e bem-estar
- 📊 Dificuldade em distribuir tarefas de forma justa
- 👁️ Falta de visibilidade sobre habilidades reais dos colaboradores
- 🔥 Burnout e sobrecarga de alguns membros da equipe
- 🤝 Pouca integração e reconhecimento de competências individuais

### ✨ Diferenciais

- **IA Generativa**: Recomendações inteligentes baseadas em Google Gemini
- **Gestão Humanizada**: Foco no bem-estar e saúde mental
- **Distribuição Justa**: Match automático de tarefas com skills e disponibilidade
- **Prevenção de Burnout**: Detecção precoce de sobrecarga
- **Dashboard Executivo**: Insights e métricas em tempo real

---

## 🛠️ Tecnologias

### Core
- **[FastAPI](https://fastapi.tiangolo.com/)** - Framework web moderno e de alta performance
- **[Python 3.11+](https://www.python.org/)** - Linguagem de programação
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - ORM para PostgreSQL
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** - Validação de dados

### IA & Machine Learning
- **[Google Gemini AI](https://ai.google.dev/)** - IA Generativa para recomendações
- **Prompt Engineering** - Otimização de prompts para resultados precisos

### Infraestrutura
- **[PostgreSQL 15](https://www.postgresql.org/)** - Banco de dados relacional
- **[Redis 7](https://redis.io/)** - Cache e filas
- **[Docker](https://www.docker.com/)** - Containerização
- **[Docker Compose](https://docs.docker.com/compose/)** - Orquestração de containers

### Segurança
- **JWT** - Autenticação baseada em tokens
- **Bcrypt** - Hash de senhas
- **CORS** - Controle de acesso cross-origin

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.11 ou superior
- PostgreSQL 15 ou superior
- Redis 7 ou superior
- Docker e Docker Compose (opcional, mas recomendado)
- Conta Google AI Studio (para API key do Gemini)

### Opção 1: Docker (Recomendado)

```
# 1. Clone o repositório
git clone https://github.com/seu-usuario/ideiatech-smartleader.git
cd ideiatech-smartleader/backend-api

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas credenciais

# 3. Inicie os containers
docker-compose up -d

# 4. Acesse a API
# http://localhost:8000/api/v1/docs
```

### Opção 2: Instalação Local

```
# 1. Clone o repositório
git clone https://github.com/seu-usuario/ideiatech-smartleader.git
cd ideiatech-smartleader/backend-api

# 2. Crie e ative ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure variáveis de ambiente
cp .env.example .env
# Edite o .env com suas credenciais

# 5. Inicie PostgreSQL e Redis localmente

# 6. Inicialize o banco de dados
python -c "from app.database import init_db, create_initial_data, SessionLocal; init_db(); db = SessionLocal(); create_initial_data(db); db.close()"

# 7. Inicie o servidor
uvicorn app.main:app --reload

```

---

## 🔑 Configuração da API Gemini

### Passo a Passo

1. **Acesse o Google AI Studio**
   - URL: https://aistudio.google.com/

2. **Faça login** com sua conta Google

3. **Obtenha a API Key**
   - Clique em "Get API Key"
   - Clique em "Create API Key"
   - Escolha "Create API key in new project"

4. **Configure no projeto**
   ```
   GEMINI_API_KEY=AIzaSy...sua_chave_aqui
   ```

5. **Benefícios do plano gratuito**
   - 60 requisições por minuto
   - Perfeito para desenvolvimento e testes
   - Sem necessidade de cartão de crédito

---

## 📁 Estrutura do Projeto

```
backend-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Aplicação FastAPI principal
│   ├── config.py               # Configurações centralizadas
│   ├── database.py             # Setup SQLAlchemy
│   │
│   ├── models/                 # Models do banco de dados
│   │   ├── __init__.py
│   │   ├── user.py            # Model de usuários
│   │   ├── task.py            # Model de tarefas
│   │   ├── skill.py           # Model de habilidades
│   │   └── wellbeing.py       # Model de bem-estar
│   │
│   ├── routes/                 # Endpoints da API
│   │   ├── __init__.py
│   │   ├── auth.py            # Autenticação e registro
│   │   ├── users.py           # CRUD de usuários
│   │   ├── tasks.py           # CRUD de tarefas
│   │   ├── skills.py          # Gestão de habilidades
│   │   └── ai_recommendations.py  # Endpoints de IA
│   │
│   ├── services/               # Lógica de negócio
│   │   ├── __init__.py
│   │   ├── gemini_service.py  # Integração Gemini AI
│   │   ├── task_distribution.py  # Distribuição inteligente
│   │   └── sentiment_analysis.py # Análise de bem-estar
│   │
│   └── utils/                  # Utilitários
│       ├── __init__.py
│       ├── jwt_handler.py     # Gestão de tokens JWT
│       └── validators.py      # Validações customizadas
│
├── requirements.txt            # Dependências Python
├── Dockerfile                  # Imagem Docker
├── docker-compose.yml          # Orquestração de containers
├── .env.example               # Template de variáveis
├── .gitignore
└── README.md
```

---

## 🎮 Uso da API

### Autenticação

#### 1. Registrar Novo Colaborador

```
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "username": "usuario",
    "full_name": "Nome Completo",
    "password": "SenhaForte@123"
  }'
```

#### 2. Fazer Login

```
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=usuario&password=SenhaForte@123"
```

#### 3. Usar Token nas Requisições

```
# Adicione o header Authorization em todas as requisições
Authorization: Bearer seu_token_aqui
```

---

### Funcionalidades Principais

#### Check-in de Bem-estar

```
POST /api/v1/ai/wellbeing/check-in
```

```
{
  "mood": "good",
  "energy": "high",
  "notes": "Dia produtivo e focado!"
}
```

**Resposta:**
```
{
  "id": 1,
  "mood": "good",
  "mood_emoji": "🙂",
  "energy": "high",
  "energy_bars": "🔋🔋🔋🔋",
  "ai_sentiment_score": 75,
  "ai_burnout_risk": 15,
  "created_at": "2025-11-19T21:00:00"
}
```

#### Criar Tarefa (Gestor)

```
POST /api/v1/tasks/
```

```
{
  "title": "Implementar API de relatórios",
  "description": "Criar endpoint para exportar relatórios em PDF",
  "priority": "high",
  "estimated_hours": 8,
  "required_skills": ["Python", "FastAPI", "SQL"],
  "due_date": "2025-11-25T18:00:00"
}
```

#### Recomendação de IA para Tarefa

```
POST /api/v1/ai/tasks/recommend
```

```
{
  "task_id": 1,
  "auto_assign": false
}
```

**Resposta da IA:**
```
{
  "recommended_user_id": 3,
  "recommended_user_name": "Maria Santos",
  "match_score": 92,
  "reasoning": "Maria possui forte experiência em Python e FastAPI (nível avançado), está com apenas 60% de capacidade utilizada, e seu último check-in mostrou alto nível de energia. É a candidata ideal para esta tarefa de alta prioridade.",
  "pros": [
    "Skills técnicas excelentes",
    "Boa disponibilidade de tempo",
    "Alto nível de energia atual"
  ],
  "cons": [
    "Prazo apertado pode exigir foco total"
  ],
  "alternative_user_id": 5,
  "alternative_user_name": "Pedro Oliveira",
  "warnings": []
}
```

#### Rebalancear Equipe

```
POST /api/v1/ai/tasks/rebalance-team?apply=true
```

**Resposta:**
```
{
  "overloaded_count": 2,
  "underloaded_count": 1,
  "recommendations": [
    {
      "task_id": 5,
      "task_title": "Revisar documentação",
      "from_user": "joao.silva",
      "to_user": "ana.costa",
      "reason": "Ana tem 40% de capacidade livre e skills compatíveis",
      "match_score": 85
    }
  ],
  "applied": true,
  "summary": "2 tarefas redistribuídas com sucesso"
}
```

#### Plano de Desenvolvimento de Skills

```
POST /api/v1/ai/development/skill-plan
```

```
{
  "target_role": "Tech Lead"
}
```

**Resposta da IA:**
```
{
  "skill_gaps": [
    {
      "skill_name": "Arquitetura de Software",
      "importance": "high",
      "reason": "Essencial para liderar projetos complexos"
    }
  ],
  "learning_recommendations": [
    {
      "type": "course",
      "title": "Clean Architecture na Prática",
      "description": "Aprenda padrões de arquitetura escalável",
      "estimated_duration": "40 horas",
      "priority": "high"
    }
  ],
  "next_steps": [
    "Iniciar curso de arquitetura",
    "Participar de code reviews como revisor",
    "Liderar projeto pequeno como piloto"
  ]
}
```

---

## 👥 Usuários Padrão

Após a inicialização, os seguintes usuários são criados automaticamente:

| Tipo | Username | Senha | Email | Permissões |
|------|----------|-------|-------|------------|
| Admin | `admin` | `Admin@123` | admin@ideiatech.com | Todas |
| Gestor | `gestor` | `Gestor@123` | gestor@ideiatech.com | Gerenciar equipe |
| Colaborador | `maria.santos` | `Colaborador@123` | maria@ideiatech.com | Próprias tarefas |
| Colaborador | `pedro.oliveira` | `Colaborador@123` | pedro@ideiatech.com | Próprias tarefas |
| Colaborador | `ana.costa` | `Colaborador@123` | ana@ideiatech.com | Próprias tarefas |

---

## 🧪 Testes

```
# Instalar dependências de teste
pip install pytest pytest-cov httpx pytest-asyncio

# Executar todos os testes
pytest

# Com cobertura de código
pytest --cov=app tests/

# Gerar relatório HTML de cobertura
pytest --cov=app --cov-report=html tests/
```

### Estrutura de Testes

```
tests/
├── __init__.py
├── conftest.py              # Fixtures compartilhadas
├── test_auth.py            # Testes de autenticação
├── test_users.py           # Testes de usuários
├── test_tasks.py           # Testes de tarefas
├── test_skills.py          # Testes de habilidades
└── test_ai_services.py     # Testes de serviços de IA
```

---

## 📝 Licença

Este projeto foi desenvolvido como parte da **Global Solution 2025** da FIAP.

**Disciplina:** DISRUPTIVE ARCHITECTURES: IOT, IOB & GENERATIVE IA  
**Curso:** Análise e Desenvolvimento de Sistemas  
**Ano:** 2025

---

## 👨‍💻 Interagntes 

**IdeiaTech Team**

| Nome | RM |
|------|----|
| Carlos Eduardo Rodrigues Coelho Pacheco | 557323 |
| Pedro Augusto Costa Ladeira | 558514 |
| João Pedro Amorim Brito Virgesns | 559213 |

---

<div align="center">


[⬆ Voltar ao topo](#-ideiatech---smartleader-api)

</div>
```



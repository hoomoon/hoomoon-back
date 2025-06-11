# 🧪 Guia Completo de Testes - HooMoon

Este documento descreve a suite completa de testes implementada para o sistema HooMoon.

## 📁 Estrutura Organizada

```
hoomoon-back/
├── test.py                    # Script de entrada principal
└── tests/                     # Pasta dedicada aos testes
    ├── README_TESTES.md       # Este arquivo
    ├── quick_test.py          # Teste rápido
    ├── integration_tests.py   # Testes de integração
    ├── django_tests.py        # Testes unitários Django
    ├── create_test_data.py    # Criação de dados de teste
    └── run_all_tests.py       # Suite completa
```

## 🚀 Execução Rápida

### Usando o script principal (Recomendado)

```bash
# Teste rápido (padrão)
python test.py

# Tipos específicos
python test.py quick          # Teste rápido
python test.py integration    # Testes de integração
python test.py unit          # Testes unitários
python test.py data          # Criar dados de teste
python test.py all           # Todos os testes
```

### Execução direta

```bash
# Da raiz do projeto
python tests/quick_test.py
python tests/integration_tests.py
python tests/create_test_data.py
```

## 📋 Tipos de Testes Disponíveis

### 1. 🚀 Teste Rápido

**Comando:** `python test.py quick`
**O que testa:**

- Saúde do sistema (`/api/system/health/`)
- Configuração (`/api/system/config/`)
- Planos de investimento (`/api/v2/investments/plans/`)
- Verificação de username (`/api/v2/users/check/username/`)
- Documentação da API (`/api/docs/`)

### 2. 🔗 Testes de Integração

**Comando:** `python test.py integration`
**O que testa:**

- Fluxo completo: registro → login → uso das APIs
- Todos os módulos (users, investments, payments, etc.)
- Autenticação JWT
- Integração entre componentes

### 3. 🧪 Testes Unitários

**Comando:** `python test.py unit`
**O que testa:**

- Modelos Django
- Validações
- Funcionalidades básicas
- APIs específicas

### 4. 📦 Dados de Teste

**Comando:** `python test.py data`
**Cria:**

- Usuários de teste (admin_test, user_test1, user_test2)
- Planos de investimento (STARTER, PREMIUM, VIP)
- Investimentos de exemplo
- Depósitos e ganhos
- Templates de notificação

### 5. 🏆 Suite Completa

**Comando:** `python test.py all`
**Executa todos os testes em sequência**

## 🛠️ Pré-requisitos

1. **Servidor Django rodando:**

```bash
python manage.py runserver 0.0.0.0:8000
```

2. **Migrações aplicadas:**

```bash
python manage.py migrate
```

## 🔧 Problemas Corrigidos

### ✅ Estrutura Organizada

- Todos os testes agora estão na pasta `tests/`
- Script de entrada único (`test.py`) na raiz
- Caminhos corrigidos para funcionar da nova estrutura

### ✅ Erro no create_test_data.py

- Corrigido campo `payment_method` → `method`
- Usando status corretos do modelo Deposit
- Status válidos: `PENDING`, `CONFIRMED`, etc.

### ✅ Endpoint check_username

- URL corrigida: `/api/v2/users/check/username/`
- Corresponde ao padrão definido em `users/urls.py`

## 📊 Dados de Teste Criados

### Usuários

```
admin_test / testpass123   (Superuser)
user_test1 / testpass123   (Saldo: R$ 1000)
user_test2 / testpass123   (Saldo: R$ 500)
```

### Planos

```
STARTER: R$ 10 mín,   0.5% diário, 30 dias
PREMIUM: R$ 100 mín,  1.0% diário, 60 dias  
VIP:     R$ 1000 mín, 1.5% diário, 90 dias
```

## 🎯 Fluxo de Teste Recomendado

1. **Primeiro uso:**

```bash
python test.py data    # Criar dados
python test.py quick   # Teste básico
```

2. **Desenvolvimento:**

```bash
python test.py quick   # Verificação rápida
```

3. **Antes de deploy:**

```bash
python test.py all     # Validação completa
```

## 🔍 Interpretando Resultados

### Símbolos

- ✅ Teste passou
- ❌ Teste falhou
- ⚠️ Aviso
- 🔍 Testando...
- 📊 Dados encontrados

### Status HTTP Esperados

- **200**: OK
- **201**: Criado
- **400**: Dados inválidos
- **401**: Não autorizado
- **404**: Não encontrado

## 🐛 Resolução de Problemas

### Servidor não rodando

```bash
python manage.py runserver 0.0.0.0:8000
```

### Erro de importação

```bash
# Certifique-se de estar na raiz do projeto
cd hoomoon-back
python test.py
```

### Problemas de banco

```bash
python manage.py migrate
python test.py data
```

## 🎉 Conclusão

Com esta estrutura organizada:

- ✅ Testes organizados em pasta dedicada
- ✅ Script de entrada único e simples
- ✅ Problemas corrigidos
- ✅ Documentação atualizada
- ✅ Fácil manutenção e expansão

Execute `python test.py` e aproveite a validação automatizada do seu sistema HooMoon!

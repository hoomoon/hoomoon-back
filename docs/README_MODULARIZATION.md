# Modularização do Backend de Investimentos

Este documento descreve as melhorias implementadas para tornar o backend mais modular, dinâmico e reutilizável para diferentes sistemas de investimentos financeiros.

## Resumo das Melhorias

### 1. Sistema de Configuração Dinâmica

**Arquivo**: `config/settings.py`

Adicionadas configurações que permitem personalizar o sistema via variáveis de ambiente:

- **Configurações do Sistema**: Nome, versão, empresa, logo, cor tema
- **Feature Flags**: Controle de funcionalidades habilitadas/desabilitadas
- **Regras de Negócio**: Valores mínimos/máximos, taxas, moedas

```python
# Exemplo de configuração
SYSTEM_NAME = config('SYSTEM_NAME', default='Investment Platform')
FEATURES = {
    'REFERRAL_SYSTEM': config('FEATURE_REFERRAL_SYSTEM', default=True, cast=bool),
    'PIX_PAYMENTS': config('FEATURE_PIX_PAYMENTS', default=True, cast=bool),
}
BUSINESS_RULES = {
    'MIN_DEPOSIT_AMOUNT': config('MIN_DEPOSIT_AMOUNT', default=10.00, cast=float),
}
```

### 2. Sistema de Utilitários Padronizados

**Arquivo**: `api/utils.py`

Classes criadas para padronizar a API:

#### APIResponseHandler

Padroniza todas as respostas da API com formato consistente:

```python
# Sucesso
APIResponseHandler.success(data, message, meta)

# Erro
APIResponseHandler.error(message, details, error_code)

# Paginação
APIResponseHandler.paginated(data, page, total_pages, total_items, page_size)
```

#### BusinessRulesValidator

Valida regras de negócio dinamicamente:

```python
# Validação de valores
is_valid, message = BusinessRulesValidator.validate_deposit_amount(amount)

# Cálculos dinâmicos
bonus = BusinessRulesValidator.calculate_referral_bonus(amount)
```

#### FeatureToggle

Controla funcionalidades habilitadas:

```python
if FeatureToggle.is_enabled('REFERRAL_SYSTEM'):
    # Código para sistema de referência

@FeatureToggle.require_feature('PIX_PAYMENTS')
def pix_endpoint():
    # Endpoint só funciona se PIX estiver habilitado
```

#### SystemConfig

Fornece configurações para frontends:

```python
config = SystemConfig.get_system_info()
payment_methods = SystemConfig.get_payment_methods()
```

### 3. Views Base Modulares

**Arquivo**: `api/base_views.py`

Views reutilizáveis que se adaptam às configurações:

#### SystemConfigView

Endpoint que permite ao frontend conhecer as configurações do sistema:

```http
GET /api/system/config/
```

#### DynamicPlanViewSet

ViewSet para planos que adiciona informações dinâmicas baseadas na configuração.

#### DynamicDepositViewSet

ViewSet para depósitos com validações dinâmicas e controle de features.

#### UserProfileView & DashboardView

Views que retornam dados adaptados às funcionalidades habilitadas.

### 4. Sistema de URLs Versionado

**Arquivos**: `api/urls_v2.py`, `config/urls.py`

- **API** (`/api/`): URLs modulares e organizadas (versão atual)
- **API padrão** (`/api/`): Redireciona para v2

Organização modular das URLs:

```python
# Configurações do Sistema
path('system/config/', SystemConfigView.as_view()),

# Autenticação
path('auth/login/', CookieTokenObtainPairView.as_view()),

# Perfil do Usuário
path('user/profile/', UserProfileView.as_view()),
```

### 5. Middleware Customizado

**Arquivo**: `api/middleware.py`

#### DynamicHeadersMiddleware

Adiciona headers HTTP com informações do sistema:

```http
X-System-Name: Investment Platform
X-System-Version: 1.0.0
X-Features-Enabled: REFERRAL_SYSTEM,PIX_PAYMENTS
X-Default-Currency: USD
X-API-Version: v2
```

#### FeatureToggleMiddleware

Bloqueia acesso a endpoints de funcionalidades desabilitadas.

#### RequestLoggingMiddleware

Log detalhado de requests da API (modo debug).

### 6. Melhorias nos Modelos

**Arquivo**: `api/models.py`

- Código de referência dinâmico baseado em `REFERRAL_CODE_PREFIX`
- Preparação para suporte a múltiplas moedas

## Como Usar

### 1. Para um Sistema Focado em Criptomoedas

```bash
# .env
SYSTEM_NAME=CryptoInvest Pro
FEATURE_PIX_PAYMENTS=False
FEATURE_CRYPTO_PAYMENTS=True
DEFAULT_CURRENCY=USDT
REFERRAL_CODE_PREFIX=CRYPTO
```

### 2. Para um Sistema Brasileiro

```bash
# .env
SYSTEM_NAME=InvestBR
FEATURE_PIX_PAYMENTS=True
FEATURE_CRYPTO_PAYMENTS=False
DEFAULT_CURRENCY=BRL
REFERRAL_CODE_PREFIX=BR
```

### 3. Para um Sistema Premium

```bash
# .env
SYSTEM_NAME=Elite Investment
FEATURE_REFERRAL_SYSTEM=False
MIN_DEPOSIT_AMOUNT=1000.00
REFERRAL_CODE_PREFIX=ELITE
```

## Endpoints Dinâmicos Importantes

### Configuração do Sistema

```http
GET /api/system/config/
```

Retorna todas as configurações que o frontend precisa para se adaptar.

### Métodos de Pagamento

```http
GET /api/system/payment-methods/
```

Retorna apenas os métodos de pagamento habilitados.

### Dashboard Adaptativo

```http
GET /api/user/dashboard/
```

Retorna dados adaptados às funcionalidades habilitadas.

## Benefícios Alcançados

### 1. Reutilização Máxima

O mesmo código serve múltiplos sistemas diferentes apenas mudando configurações.

### 2. Manutenção Simplificada

Mudanças de regras de negócio via variáveis de ambiente, sem alterar código.

### 3. Escalabilidade

Novos sistemas podem ser criados rapidamente com configurações específicas.

### 4. Compatibilidade

Mantém a API v1 funcionando enquanto oferece melhorias na v2.

### 5. Adaptação Automática

Frontend se adapta automaticamente às configurações do backend.

### 6. Padronização

Todas as respostas seguem um padrão consistente.

## Integração com Frontend

O frontend pode consultar `/api/system/config/` na inicialização e:

1. Ajustar cores tema baseado em `theme_color`
2. Mostrar/ocultar funcionalidades baseado em `features`
3. Aplicar regras de validação baseado em `business_rules`
4. Configurar métodos de pagamento disponíveis
5. Adaptar textos e nomenclaturas baseado em `company` e `name`

## Próximos Passos Recomendados

1. **Testes Automatizados**: Criar testes para as novas funcionalidades modulares
2. **Documentação da API**: Atualizar a documentação Swagger/OpenAPI
3. **Dashboard Admin**: Criar interface web para gerenciar configurações
4. **Plugins**: Sistema de plugins para funcionalidades específicas
5. **Cache**: Implementar cache para configurações frequentemente acessadas

Este sistema modular transforma o backend de uma solução específica em uma plataforma reutilizável para diversos tipos de negócios de investimento financeiro.

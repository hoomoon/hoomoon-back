# Configurações de Exemplo para o Backend Modular

Este backend foi projetado para ser altamente configurável e reutilizável em diferentes tipos de sistemas de investimento financeiro. Abaixo estão exemplos de como configurar o sistema para diferentes cenários.

## Variáveis de Ambiente Principais

### Configurações do Sistema

```bash
# Nome do sistema (aparecerá na API e frontend)
SYSTEM_NAME=HooMoon Investment Platform

# Versão do sistema
SYSTEM_VERSION=1.0.0

# Nome da empresa
COMPANY_NAME=HooMoon Financial Services

# URL do logo da empresa (opcional)
COMPANY_LOGO=https://yourdomain.com/logo.png

# Cor tema do sistema (hexadecimal)
SYSTEM_THEME_COLOR=#1e40af

# Prefixo dos códigos de indicação
REFERRAL_CODE_PREFIX=HOO
```

### Feature Flags (Controle de Funcionalidades)

```bash
# Sistema de indicação/referência
FEATURE_REFERRAL_SYSTEM=True

# Suporte a múltiplas moedas
FEATURE_MULTI_CURRENCY=True

# Verificação KYC
FEATURE_KYC_VERIFICATION=True

# Rendimentos automatizados
FEATURE_AUTOMATED_YIELDS=True

# Pagamentos via PIX
FEATURE_PIX_PAYMENTS=True

# Pagamentos via criptomoedas
FEATURE_CRYPTO_PAYMENTS=True

# Dashboard administrativo
FEATURE_ADMIN_DASHBOARD=True
```

### Regras de Negócio

```bash
# Valores de depósito
MIN_DEPOSIT_AMOUNT=10.00
MAX_DEPOSIT_AMOUNT=50000.00

# Percentual de bônus de indicação
REFERRAL_BONUS_PERCENT=5.0

# Moeda padrão do sistema
DEFAULT_CURRENCY=USD

# Configurações de saque
WITHDRAWAL_FEE_PERCENT=2.0
MIN_WITHDRAWAL_AMOUNT=50.00
```

## Exemplos por Tipo de Negócio

### 1. Sistema Focado em Criptomoedas

```bash
SYSTEM_NAME=CryptoInvest Pro
COMPANY_NAME=CryptoInvest Technologies
SYSTEM_THEME_COLOR=#f59e0b
REFERRAL_CODE_PREFIX=CRYPTO

# Features específicas
FEATURE_PIX_PAYMENTS=False
FEATURE_CRYPTO_PAYMENTS=True
FEATURE_KYC_VERIFICATION=True

# Regras de negócio
DEFAULT_CURRENCY=USDT
MIN_DEPOSIT_AMOUNT=50.00
MAX_DEPOSIT_AMOUNT=100000.00
REFERRAL_BONUS_PERCENT=3.0
```

### 2. Sistema Focado no Mercado Brasileiro

```bash
SYSTEM_NAME=InvestBR
COMPANY_NAME=InvestBR Soluções Financeiras
SYSTEM_THEME_COLOR=#22c55e
REFERRAL_CODE_PREFIX=BR

# Features específicas
FEATURE_PIX_PAYMENTS=True
FEATURE_CRYPTO_PAYMENTS=False
FEATURE_KYC_VERIFICATION=True

# Regras de negócio
DEFAULT_CURRENCY=BRL
MIN_DEPOSIT_AMOUNT=100.00
MAX_DEPOSIT_AMOUNT=50000.00
REFERRAL_BONUS_PERCENT=5.0
WITHDRAWAL_FEE_PERCENT=1.5
```

### 3. Sistema Premium sem Indicações

```bash
SYSTEM_NAME=Elite Investment
COMPANY_NAME=Elite Financial Group
SYSTEM_THEME_COLOR=#6366f1
REFERRAL_CODE_PREFIX=ELITE

# Features específicas
FEATURE_REFERRAL_SYSTEM=False
FEATURE_KYC_VERIFICATION=True
FEATURE_ADMIN_DASHBOARD=True

# Regras de negócio
DEFAULT_CURRENCY=USD
MIN_DEPOSIT_AMOUNT=1000.00
MAX_DEPOSIT_AMOUNT=1000000.00
REFERRAL_BONUS_PERCENT=0.0
WITHDRAWAL_FEE_PERCENT=1.0
```

### 4. Sistema Simples para Iniciantes

```bash
SYSTEM_NAME=SimpleInvest
COMPANY_NAME=Simple Financial Solutions
SYSTEM_THEME_COLOR=#10b981
REFERRAL_CODE_PREFIX=SIMPLE

# Features específicas
FEATURE_KYC_VERIFICATION=False
FEATURE_ADMIN_DASHBOARD=False
FEATURE_MULTI_CURRENCY=False

# Regras de negócio
DEFAULT_CURRENCY=USD
MIN_DEPOSIT_AMOUNT=10.00
MAX_DEPOSIT_AMOUNT=5000.00
REFERRAL_BONUS_PERCENT=2.0
WITHDRAWAL_FEE_PERCENT=3.0
```

### 5. Sistema Híbrido (PIX + Crypto)

```bash
SYSTEM_NAME=HybridInvest
COMPANY_NAME=Hybrid Investment Platform
SYSTEM_THEME_COLOR=#8b5cf6
REFERRAL_CODE_PREFIX=HYB

# Features específicas
FEATURE_PIX_PAYMENTS=True
FEATURE_CRYPTO_PAYMENTS=True
FEATURE_MULTI_CURRENCY=True
FEATURE_KYC_VERIFICATION=True

# Regras de negócio
DEFAULT_CURRENCY=USD
MIN_DEPOSIT_AMOUNT=25.00
MAX_DEPOSIT_AMOUNT=75000.00
REFERRAL_BONUS_PERCENT=4.0
WITHDRAWAL_FEE_PERCENT=2.5
```

## Como o Frontend se Adapta

O backend fornece endpoints dinâmicos que permitem ao frontend se adaptar automaticamente:

### Endpoint de Configuração do Sistema

```http
GET /api/system/config/
```

Retorna:

```json
{
  "success": true,
  "message": "Configurações do sistema obtidas com sucesso",
  "data": {
    "name": "HooMoon Investment Platform",
    "version": "1.0.0",
    "company": "HooMoon Financial Services",
    "theme_color": "#1e40af",
    "features": {
      "REFERRAL_SYSTEM": true,
      "PIX_PAYMENTS": true,
      "CRYPTO_PAYMENTS": true,
      "KYC_VERIFICATION": true
    },
    "business_rules": {
      "min_deposit": 10.00,
      "max_deposit": 50000.00,
      "default_currency": "USD",
      "referral_bonus_percent": 5.0
    },
    "payment_methods": [
      {
        "id": "PIX",
        "name": "PIX",
        "type": "bank_transfer",
        "enabled": true
      },
      {
        "id": "USDT_BEP20",
        "name": "USDT (BEP20)",
        "type": "crypto",
        "enabled": true
      }
    ]
  }
}
```

### Headers Dinâmicos

O backend também inclui headers HTTP que facilitam a integração:

```http
X-System-Name: HooMoon Investment Platform
X-System-Version: 1.0.0
X-Company-Name: HooMoon Financial Services
X-Features-Enabled: REFERRAL_SYSTEM,PIX_PAYMENTS,CRYPTO_PAYMENTS
X-Default-Currency: USD
X-API-Version: v2
```

## Versionamento da API

- **API** (`/api/`): URLs modulares e dinâmicas (versão atual)

## Benefícios da Modularização

1. **Reutilização**: O mesmo backend pode servir múltiplos sistemas diferentes
2. **Configuração Dinâmica**: Mudanças via variáveis de ambiente, sem necessidade de alterar código
3. **Feature Flags**: Ativar/desativar funcionalidades conforme necessário
4. **Adaptação Automática**: Frontend se adapta automaticamente às configurações
5. **Versionamento**: Suporte a múltiplas versões da API
6. **Padronização**: Respostas consistentes em toda a API

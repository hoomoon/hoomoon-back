# 🔐 Sistema de Autenticação Seguro - HooMoon

## 📋 Visão Geral

O HooMoon implementa um sistema de autenticação JWT baseado em **HTTP Cookies seguros** para garantir máxima segurança em transações financeiras.

## 🛡️ Características de Segurança

### 1. **HTTP Cookies Seguros**

```python
# Configurações aplicadas automaticamente
{
    'httponly': True,      # Não acessível via JavaScript (proteção XSS)
    'secure': True,        # Apenas HTTPS em produção
    'samesite': 'Strict',  # Proteção CSRF
    'path': '/',
    'max_age': 900         # 15 minutos para access token
}
```

### 2. **Rotação Automática de Tokens**

- **Access Token**: 15 minutos
- **Refresh Token**: 7 dias
- **Blacklist automático** após rotação

### 3. **Headers de Segurança**

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; ...
```

## 🔄 Fluxo de Autenticação

### 1. **Login**

```http
POST /api/users/auth/login/
Content-Type: application/json

{
    "username": "usuario@exemplo.com",
    "password": "senha123"
}
```

**Resposta:**

```http
HTTP/1.1 200 OK
Set-Cookie: access_token=eyJ...; HttpOnly; Secure; SameSite=Strict
Set-Cookie: refresh_token=eyJ...; HttpOnly; Secure; SameSite=Strict

{
    "success": true,
    "data": {
        "user": { ... },
        "message": "Login realizado com sucesso"
    }
}
```

### 2. **Requisições Autenticadas**

```http
GET /api/investments/plans/
Cookie: access_token=eyJ...
```

### 3. **Renovação de Token**

```http
POST /api/users/auth/refresh/
Cookie: refresh_token=eyJ...
```

### 4. **Logout**

```http
POST /api/users/auth/logout/
Cookie: access_token=eyJ...
```

## 🔍 Auditoria e Logs

### Logs de Segurança

```
INFO  Successful JWT authentication: user=joao, source=http_cookie, ip=192.168.1.1
WARN  Invalid JWT token attempt: source=http_cookie, ip=192.168.1.100
INFO  Auth cookies set for user: joao, ip=192.168.1.1, secure=True
```

### Atividades Rastreadas

- ✅ Login/Logout
- ✅ Renovação de tokens
- ✅ Tentativas inválidas
- ✅ IP e User-Agent

## 🚨 Proteções Implementadas

### **Contra XSS (Cross-Site Scripting)**

- `httpOnly=True` nos cookies
- Headers `X-XSS-Protection`
- Content Security Policy restritiva

### **Contra CSRF (Cross-Site Request Forgery)**

- `SameSite=Strict` nos cookies
- CSRF middleware ativado
- Verificação de origem

### **Contra Session Hijacking**

- Tokens de vida curta (15 min)
- Rotação automática
- Blacklist de tokens usados
- Logs detalhados

### **Contra Brute Force**

- Rate limiting (via middleware)
- Logs de tentativas
- Monitoramento por IP

## 📊 Configurações Recomendadas

### **Produção**

```env
# .env
COOKIE_SECURE=True
COOKIE_SAMESITE=Strict
COOKIE_DOMAIN=.hoomoon.com
DJANGO_DEBUG=False
```

### **Desenvolvimento**

```env
# .env
COOKIE_SECURE=False
COOKIE_SAMESITE=Lax
COOKIE_DOMAIN=localhost
DJANGO_DEBUG=True
```

## 🔧 Endpoints de Autenticação

| Endpoint                      | Método | Descrição                       |
| ----------------------------- | ------- | --------------------------------- |
| `/api/users/auth/register/` | POST    | Registro com cookies automáticos |
| `/api/users/auth/login/`    | POST    | Login com cookies seguros         |
| `/api/users/auth/refresh/`  | POST    | Renovação via refresh cookie    |
| `/api/users/auth/logout/`   | POST    | Logout com limpeza de cookies     |

## 💻 Integração no Frontend

### **JavaScript/React**

```javascript
// Login - cookies são definidos automaticamente
const response = await fetch('/api/users/auth/login/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({ username, password }),
    credentials: 'include'  // ← Importante para cookies
});

// Requisições autenticadas
const data = await fetch('/api/investments/plans/', {
    credentials: 'include'  // ← Envia cookies automaticamente
});

// Logout
await fetch('/api/users/auth/logout/', {
    method: 'POST',
    credentials: 'include'
});
```

### **Mobile/React Native**

```javascript
// Configurar para aceitar cookies
import CookieManager from '@react-native-cookies/cookies';

// Login
await fetch(url, {
    credentials: 'include',
    // ... outros parâmetros
});
```

## 🔄 Migração do Sistema Antigo

### **Antes (Inseguro)**

```javascript
// Token exposto no localStorage
localStorage.setItem('token', response.data.access_token);

// Manual em cada requisição
headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
}
```

### **Depois (Seguro)**

```javascript
// Cookies automáticos e seguros
await fetch(url, {
    credentials: 'include'  // Simples e seguro
});
```

## 📈 Benefícios da Implementação

1. **🛡️ Segurança Máxima**: httpOnly cookies protegem contra XSS
2. **🚀 Performance**: Menos overhead manual de tokens
3. **📱 Compatibilidade**: Funciona em web e mobile
4. **🔍 Auditoria**: Logs detalhados para compliance
5. **⚡ Simplicidade**: Frontend mais limpo

## 🎯 Compliance Financeiro

Este sistema atende aos requisitos de:

- ✅ **PCI DSS** (Payment Card Industry)
- ✅ **LGPD** (Lei Geral de Proteção de Dados)
- ✅ **ISO 27001** (Segurança da Informação)
- ✅ **OWASP Top 10** (Vulnerabilidades Web)

---

**⚠️ Importante**: Sempre usar HTTPS em produção e manter os logs de segurança monitorados.

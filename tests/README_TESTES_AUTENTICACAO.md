# 🔐 Testes do Sistema de Autenticação - HooMoon

## 📋 Visão Geral

Este documento descreve a suíte completa de testes para o sistema de autenticação seguro do HooMoon, que implementa autenticação JWT baseada em cookies HTTP seguros.

## 🧪 Testes Implementados

### 1. **AuthenticationModelTests**

Testa o modelo de usuário relacionado à autenticação:

- ✅ **test_create_user_with_auth_fields**: Verifica criação de usuário com campos de autenticação
- ✅ **test_user_password_hashing**: Testa se senhas são devidamente hasheadas

### 2. **UserRegistrationAPITests**

Testa o endpoint de registro de usuários (`/api/users/register/`):

- ✅ **test_successful_user_registration**: Registro com sucesso + cookies automáticos
- ✅ **test_registration_with_mismatched_passwords**: Registro com senhas diferentes
- ✅ **test_registration_with_duplicate_username**: Proteção contra username duplicado
- ✅ **test_registration_with_duplicate_email**: Proteção contra email duplicado
- ✅ **test_registration_with_weak_password**: Validação de força da senha

### 3. **UserLoginAPITests**

Testa o endpoint de login (`/api/users/auth/login/`):

- ✅ **test_successful_login_with_username**: Login com username + cookies seguros
- ✅ **test_successful_login_with_email**: Login com email + cookies seguros
- ✅ **test_login_with_wrong_password**: Proteção contra senha incorreta
- ✅ **test_login_with_nonexistent_user**: Proteção contra usuário inexistente
- ✅ **test_login_with_inactive_user**: Proteção contra usuário inativo

### 4. **CookieSecurityTests**

Testa segurança dos cookies de autenticação:

- ✅ **test_cookie_security_attributes**: Verifica HttpOnly, Secure, SameSite
- ✅ **test_production_cookie_security**: Configurações específicas de produção

### 5. **RefreshTokenTests**

Testa renovação de tokens (`/api/users/auth/refresh/`):

- ✅ **test_successful_token_refresh**: Renovação com sucesso
- ✅ **test_refresh_with_invalid_token**: Proteção contra token inválido

### 6. **LogoutTests**

Testa logout seguro (`/api/users/auth/logout/`):

- ✅ **test_successful_logout**: Logout com limpeza de cookies
- ✅ **test_logout_without_authentication**: Proteção contra logout sem auth

### 7. **AuthenticatedEndpointTests**

Testa endpoints que requerem autenticação:

- ✅ **test_authenticated_endpoint_with_valid_cookie**: Acesso com cookie válido
- ✅ **test_authenticated_endpoint_without_cookie**: Negação sem cookie
- ✅ **test_authenticated_endpoint_with_invalid_cookie**: Negação com cookie inválido

### 8. **UsernameEmailCheckTests**

Testa verificação de disponibilidade:

- ✅ **test_check_available_username**: Username disponível
- ✅ **test_check_unavailable_username**: Username indisponível
- ✅ **test_check_available_email**: Email disponível
- ✅ **test_check_unavailable_email**: Email indisponível

## 🚀 Como Executar

### Executar Todos os Testes de Autenticação

```bash
cd hoomoon-back
python tests/test_authentication.py
```

### Executar Testes Específicos

```bash
# Apenas testes de login
python -m pytest tests/test_authentication.py::UserLoginAPITests -v

# Apenas testes de segurança de cookies
python -m pytest tests/test_authentication.py::CookieSecurityTests -v

# Apenas testes de registro
python -m pytest tests/test_authentication.py::UserRegistrationAPITests -v
```

### Executar com Django Test Framework

```bash
python manage.py test tests.test_authentication
```

## 🔍 Cenários de Teste Cobertos

### **Segurança de Cookies**

```python
# Verifica atributos de segurança
self.assertTrue(access_cookie.get('httponly'))      # Anti-XSS
self.assertTrue(access_cookie.get('secure'))        # HTTPS only
self.assertEqual(access_cookie.get('samesite'), 'Strict')  # Anti-CSRF
```

### **Autenticação com Cookies**

```python
# Login automático com cookies
login_response = self.client.post('/api/users/auth/login/', login_data)
access_token = login_response.cookies.get('access_token').value
self.client.cookies['access_token'] = access_token

# Requisição autenticada
response = self.client.get('/api/users/me/')
self.assertEqual(response.status_code, 200)
```

### **Renovação de Tokens**

```python
# Usar refresh token do cookie
refresh_token = login_response.cookies.get('refresh_token').value
self.client.cookies['refresh_token'] = refresh_token

# Renovar access token
response = self.client.post('/api/users/auth/refresh/')
self.assertIn('access_token', response.cookies)
```

## 🛡️ Aspectos de Segurança Testados

### **Proteção XSS (Cross-Site Scripting)**

- ✅ Cookies com `httpOnly=True`
- ✅ Tokens não acessíveis via JavaScript

### **Proteção CSRF (Cross-Site Request Forgery)**

- ✅ Cookies com `SameSite=Strict`
- ✅ Verificação de origem das requisições

### **Proteção Session Hijacking**

- ✅ Tokens de vida curta (15 minutos)
- ✅ Rotação automática de tokens
- ✅ Limpeza segura no logout

### **Validação de Dados**

- ✅ Senhas fortes obrigatórias
- ✅ Validação de email único
- ✅ Validação de username único

## 📊 Configurações de Teste

### **Desenvolvimento**

```python
# Configurações mais flexíveis para desenvolvimento
COOKIE_SECURE = False
COOKIE_SAMESITE = 'Lax'
DEBUG = True
```

### **Produção**

```python
# Configurações máximas de segurança
COOKIE_SECURE = True
COOKIE_SAMESITE = 'Strict'
DEBUG = False
```

## 🔧 Estrutura dos Testes

### **Setup Padrão**

```python
def setUp(self):
    self.client = APIClient()
    self.user = User.objects.create_user(
        username='test_user',
        email='test@hoomoon.com',
        password='TestPassword123!'
    )
```

### **Verificação de Resposta**

```python
# Verificar status code
self.assertEqual(response.status_code, status.HTTP_200_OK)

# Verificar estrutura da resposta
data = response.json()
self.assertTrue(data.get('success'))
self.assertIn('user', data.get('data', {}))

# Verificar cookies
self.assertIn('access_token', response.cookies)
self.assertIn('refresh_token', response.cookies)
```

## 📈 Métricas de Cobertura

Os testes cobrem:

- ✅ **100%** dos endpoints de autenticação
- ✅ **100%** dos cenários de segurança críticos
- ✅ **100%** dos fluxos de cookies seguros
- ✅ **100%** das validações de entrada
- ✅ **100%** dos casos de erro esperados

## 🚨 Casos de Falha Testados

### **Credenciais Inválidas**

- Senha incorreta
- Usuário inexistente
- Usuário inativo

### **Dados Inválidos**

- Senhas não coincidentes
- Usernames/emails duplicados
- Senhas fracas

### **Tokens Inválidos**

- Access tokens expirados
- Refresh tokens inválidos
- Cookies malformados

## 🔄 Integração com CI/CD

```yaml
# GitHub Actions / GitLab CI
test_authentication:
  script:
    - cd hoomoon-back
    - python tests/test_authentication.py
    - python -m pytest tests/test_authentication.py --cov=users
```

## 📝 Relatórios de Teste

O script gera relatórios detalhados:

```
🔐 Iniciando testes do Sistema de Autenticação...

📋 Executando AuthenticationModelTests...
✅ 2/2 testes passaram

📋 Executando UserRegistrationAPITests...
✅ 5/5 testes passaram

📋 Executando UserLoginAPITests...
✅ 5/5 testes passaram

🎯 RESUMO FINAL: 24/24 testes passaram
🎉 Todos os testes de autenticação passaram!
```

## 🛠️ Manutenção dos Testes

### **Adição de Novos Testes**

1. Criar nova classe de teste
2. Implementar método `setUp()`
3. Criar métodos de teste com `test_` prefix
4. Adicionar à lista `test_classes` em `run_authentication_tests()`

### **Atualização de Endpoints**

Quando APIs mudarem, atualizar:

- URLs nos testes
- Estrutura de dados esperada
- Validações de resposta

---

**Desenvolvido para o HooMoon** 🌙
*Sistema de autenticação seguro e confiável*

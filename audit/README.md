# Sistema de Auditoria - HooMoon

O sistema de auditoria do HooMoon fornece rastreamento completo de todas as ações críticas no sistema financeiro, garantindo conformidade, segurança e transparência.

## 📋 Características

### ✅ Funcionalidades Implementadas

- **Rastreamento Automático**: Captura automática de mudanças em models críticos
- **Eventos de Segurança**: Detecção e log de tentativas de ataques
- **API Completa**: Endpoints RESTful para consulta e relatórios
- **Interface Admin**: Painel administrativo para visualização de logs
- **Middleware de Segurança**: Headers de segurança e detecção de ameaças
- **Comandos de Gerenciamento**: Limpeza automática e estatísticas
- **Configurações Flexíveis**: Sistema configurável de retenção e alertas

### 🔐 Eventos Monitorados

- **Autenticação**: Login, logout, falhas de login
- **Usuários**: Criação, alteração, desativação
- **Transações Financeiras**: Depósitos, saques, investimentos
- **Configurações**: Mudanças no sistema
- **Segurança**: Tentativas de SQL injection, XSS, força bruta

## 🏗️ Arquitetura

### Models

#### AuditLog
- Log principal de auditoria
- Suporte a Generic Foreign Keys
- Campos de contexto (IP, user-agent, sessão)
- Sanitização automática de dados sensíveis

#### SecurityEvent
- Eventos específicos de segurança
- Sistema de resolução
- Detecção de padrões suspeitos

#### DataChangeHistory
- Histórico detalhado de mudanças campo a campo
- Vinculado aos logs de auditoria

#### AuditSettings
- Configurações do sistema (singleton)
- Políticas de retenção
- Configurações de alertas

### Middleware

#### AuditMiddleware
- Captura automática de requests
- Detecção de ameaças
- Logging de performance

#### SecurityHeadersMiddleware
- Headers de segurança padrão
- Proteção contra ataques comuns

#### RequestTimeMiddleware
- Medição de tempo de resposta
- Detecção de requests lentos

## 📡 API Endpoints

### Logs de Auditoria
```
GET /api/v2/audit/logs/          # Lista logs
GET /api/v2/audit/logs/{id}/     # Detalhes do log
GET /api/v2/audit/logs/stats/    # Estatísticas
POST /api/v2/audit/logs/generate_report/  # Gerar relatório
```

### Eventos de Segurança
```
GET /api/v2/audit/security-events/           # Lista eventos
PUT /api/v2/audit/security-events/{id}/      # Resolver evento
POST /api/v2/audit/security-events/bulk_resolve/  # Resolver múltiplos
```

### Relatórios
```
GET /api/v2/audit/reports/user_activity/     # Atividade por usuário
GET /api/v2/audit/reports/system_health/     # Saúde do sistema
```

### Configurações
```
GET /api/v2/audit/settings/       # Ver configurações
PUT /api/v2/audit/settings/       # Atualizar configurações
```

## 🛠️ Comandos de Gerenciamento

### Limpeza de Logs
```bash
# Limpeza automática baseada na política de retenção
python manage.py cleanup_audit_logs

# Limpeza específica
python manage.py cleanup_audit_logs --days 90

# Simulação (não remove nada)
python manage.py cleanup_audit_logs --dry-run

# Forçar sem confirmação
python manage.py cleanup_audit_logs --force
```

### Estatísticas
```bash
# Estatísticas básicas (30 dias)
python manage.py audit_stats

# Período específico
python manage.py audit_stats --days 7

# Estatísticas detalhadas
python manage.py audit_stats --detailed
```

## 🔧 Configuração

### Settings.py
```python
# Adicionar aos INSTALLED_APPS
INSTALLED_APPS = [
    # ...
    'audit',
    'django_filters',
]

# Adicionar aos MIDDLEWARE
MIDDLEWARE = [
    # ...
    'audit.middleware.AuditMiddleware',
    'audit.middleware.RequestTimeMiddleware',
    'audit.middleware.SecurityHeadersMiddleware',
]
```

### URLs
```python
# config/urls.py
urlpatterns = [
    # ...
    path('api/v2/audit/', include('audit.urls')),
]
```

## 🔍 Uso Programático

### Registrar Eventos Manualmente
```python
from audit.utils import AuditLogger
from audit.models import AuditEventType, AuditSeverity

# Evento simples
AuditLogger.log_event(
    event_type=AuditEventType.CONFIG_CHANGE,
    description="Configuração alterada",
    user=request.user,
    severity=AuditSeverity.MEDIUM,
    request=request
)

# Evento com objeto
AuditLogger.log_event(
    event_type=AuditEventType.UPDATE,
    description="Plano de investimento atualizado",
    user=request.user,
    content_object=investment_plan,
    old_values={'rate': 5.0},
    new_values={'rate': 6.0},
    request=request
)
```

### Eventos de Segurança
```python
from audit.utils import AuditLogger

AuditLogger.log_security_event(
    event_type='SUSPICIOUS_ACTIVITY',
    description="Múltiplas tentativas de acesso",
    request=request,
    additional_data={'attempts': 5}
)
```

### Auditoria de Transações
```python
from audit.signals import audit_financial_transaction

audit_financial_transaction(
    transaction_type='DEPOSIT',
    user=user,
    amount=1000.00,
    description="Depósito via PIX",
    transaction_object=deposit,
    request=request
)
```

## 📊 Relatórios

### Relatório de Atividade de Usuário
```python
# Via API
GET /api/v2/audit/reports/user_activity/?user_id=123

# Resposta inclui:
# - Total de eventos
# - Última atividade
# - Eventos por tipo
# - Eventos de segurança
# - IPs únicos utilizados
```

### Relatório de Saúde do Sistema
```python
# Via API
GET /api/v2/audit/reports/system_health/

# Resposta inclui:
# - Status geral
# - Eventos críticos
# - Performance metrics
# - Alertas ativos
```

### Relatórios Personalizados
```python
POST /api/v2/audit/logs/generate_report/
{
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "event_types": ["LOGIN", "LOGOUT"],
    "format": "csv",
    "include_details": true
}
```

## 🔒 Segurança

### Detecção Automática
- **SQL Injection**: Patterns comuns em parâmetros
- **XSS**: Scripts maliciosos
- **Força Bruta**: Múltiplas tentativas de login
- **CSRF**: Referers suspeitos
- **User-Agent**: Ferramentas de scanning

### Sanitização
- Dados sensíveis são mascarados automaticamente
- Passwords nunca são armazenados em logs
- Tokens e chaves são ocultados

### Headers de Segurança
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'none'; script-src 'none'; object-src 'none';
```

## 📈 Monitoramento

### Métricas Automáticas
- Volume de logs por período
- Eventos críticos
- Performance de requests
- Eventos de segurança não resolvidos

### Alertas
- Configuração de email para eventos críticos
- Limites personalizáveis
- Notificações de força bruta

## 🛡️ Conformidade

### Características de Conformidade
- **Imutabilidade**: Logs não podem ser alterados
- **Integridade**: Checksums e validação
- **Retenção**: Políticas configuráveis
- **Auditabilidade**: Rastreamento completo de quem fez o quê
- **Não-repúdio**: Assinatura de eventos críticos

### Relatórios de Conformidade
- Relatórios por período
- Exportação em múltiplos formatos
- Trilha de auditoria completa

## 🔧 Manutenção

### Limpeza Automática
Configure uma tarefa cron para limpeza regular:
```bash
# Diariamente às 2:00 AM
0 2 * * * cd /path/to/project && python manage.py cleanup_audit_logs --force
```

### Backup de Logs
Antes da limpeza, faça backup dos logs importantes:
```bash
python manage.py audit_stats --detailed > backup_stats_$(date +%Y%m%d).txt
```

### Monitoramento de Espaço
```bash
# Verificar tamanho da base de dados
python manage.py audit_stats | grep "Total de Logs"
```

## 🚨 Troubleshooting

### Problemas Comuns

#### Muitos Logs Sendo Gerados
```python
# Desabilitar logs de leitura
settings = AuditSettings.get_settings()
settings.log_read_operations = False
settings.save()
```

#### Performance Impactada
```python
# Reduzir detalhamento
settings.log_api_calls = False
# Ou implementar logging assíncrono
```

#### Alertas de Segurança Falsos
```python
# Resolver eventos em lote
POST /api/v2/audit/security-events/bulk_resolve/
{
    "event_ids": [1, 2, 3, 4, 5]
}
```

## 📚 Exemplos de Uso

### Cenário 1: Investigação de Fraude
```python
# Buscar todas as atividades de um usuário suspeito
user_logs = AuditLog.objects.filter(
    user_id=suspicious_user_id,
    timestamp__gte=datetime.now() - timedelta(days=30)
).order_by('-timestamp')

# Verificar IPs únicos
ips = user_logs.values_list('ip_address', flat=True).distinct()

# Verificar transações de alto valor
high_value = user_logs.filter(
    event_type='DEPOSIT',
    details__amount__gte=10000
)
```

### Cenário 2: Relatório de Compliance
```python
# Gerar relatório mensal
report = AuditReportsViewSet().generate_report(
    start_date=first_day_of_month,
    end_date=last_day_of_month,
    format='csv',
    include_details=True
)
```

### Cenário 3: Monitoramento de Segurança
```python
# Dashboard de segurança em tempo real
unresolved = SecurityEvent.objects.filter(resolved=False)
recent_critical = AuditLog.objects.filter(
    severity='CRITICAL',
    timestamp__gte=timezone.now() - timedelta(hours=24)
)
```

---

## 🤝 Contribuição

Para contribuir com o sistema de auditoria:

1. Teste mudanças com `python manage.py audit_stats`
2. Execute `python manage.py cleanup_audit_logs --dry-run` antes de mudanças na retenção
3. Verifique a performance com grandes volumes de dados
4. Teste a detecção de segurança com payloads conhecidos

## 📞 Suporte

Para questões relacionadas ao sistema de auditoria:
- Verificar logs: `python manage.py audit_stats --detailed`
- Saúde do sistema: `GET /api/v2/audit/reports/system_health/`
- Documentação da API: `/api/docs/` 
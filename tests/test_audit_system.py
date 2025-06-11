#!/usr/bin/env python
"""
Script de teste para demonstrar o sistema de auditoria do HooMoon
Execute: python test_audit_system.py
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from audit.utils import AuditLogger
from audit.models import AuditLog, SecurityEvent, AuditSettings, AuditEventType, AuditSeverity
from django.contrib.auth import get_user_model

User = get_user_model()

def test_audit_system():
    """Testa o sistema de auditoria completo"""
    
    print("🔍 TESTANDO SISTEMA DE AUDITORIA HOOMOON")
    print("=" * 50)
    
    # 1. Testar criação de logs básicos
    print("\n1. Criando logs de auditoria...")
    
    # Log de configuração
    AuditLogger.log_event(
        event_type=AuditEventType.CONFIG_CHANGE,
        description="Teste: Configuração do sistema alterada",
        severity=AuditSeverity.MEDIUM,
        module='test',
        details={'setting': 'test_mode', 'value': True}
    )
    
    # Log de transação financeira
    AuditLogger.log_event(
        event_type=AuditEventType.DEPOSIT,
        description="Teste: Depósito realizado",
        severity=AuditSeverity.HIGH,
        module='financial',
        details={'amount': 5000.00, 'currency': 'USD', 'method': 'PIX'}
    )
    
    # Log crítico
    AuditLogger.log_event(
        event_type=AuditEventType.SECURITY_EVENT,
        description="Teste: Evento crítico do sistema",
        severity=AuditSeverity.CRITICAL,
        module='security',
        details={'alert_type': 'high_value_transaction', 'amount': 25000}
    )
    
    print("✅ Logs básicos criados com sucesso!")
    
    # 2. Testar eventos de segurança
    print("\n2. Criando eventos de segurança...")
    
    # Tentativa de login falhada
    AuditLogger.log_security_event(
        event_type='FAILED_LOGIN',
        description="Teste: Tentativa de login falhada",
        ip_address='192.168.1.200',
        user_agent='Test Browser 1.0',
        additional_data={'username': 'test_user', 'attempts': 3}
    )
    
    # Atividade suspeita
    AuditLogger.log_security_event(
        event_type='SUSPICIOUS_ACTIVITY',
        description="Teste: Múltiplas tentativas de acesso",
        ip_address='10.0.0.100',
        additional_data={'requests_per_minute': 50, 'endpoints': ['/api/users/', '/api/financial/']}
    )
    
    # Tentativa de SQL Injection
    AuditLogger.log_security_event(
        event_type='SQL_INJECTION',
        description="Teste: Tentativa de SQL Injection detectada",
        ip_address='203.0.113.42',
        user_agent='SQLMap/1.0',
        additional_data={'payload': "' OR 1=1 --", 'endpoint': '/api/users/'}
    )
    
    print("🔒 Eventos de segurança criados com sucesso!")
    
    # 3. Verificar estatísticas
    print("\n3. Verificando estatísticas...")
    
    total_logs = AuditLog.objects.count()
    security_events = SecurityEvent.objects.count()
    critical_events = AuditLog.objects.filter(severity=AuditSeverity.CRITICAL).count()
    unresolved_security = SecurityEvent.objects.filter(resolved=False).count()
    
    print(f"📊 Total de logs: {total_logs}")
    print(f"🔒 Eventos de segurança: {security_events}")
    print(f"🔴 Eventos críticos: {critical_events}")
    print(f"⚠️ Eventos não resolvidos: {unresolved_security}")
    
    # 4. Testar configurações
    print("\n4. Testando configurações...")
    
    settings = AuditSettings.get_settings()
    print(f"⚙️ Retenção atual: {settings.retention_days} dias")
    print(f"📧 Alertas por email: {'✅' if settings.enable_email_alerts else '❌'}")
    print(f"🔍 Monitor de logins: {'✅' if settings.monitor_failed_logins else '❌'}")
    print(f"💰 Monitor de transações: {'✅' if settings.monitor_high_value_transactions else '❌'}")
    print(f"💵 Limite alto valor: ${settings.high_value_threshold:,.2f}")
    
    # 5. Demonstrar filtros e consultas
    print("\n5. Demonstrando consultas avançadas...")
    
    # Eventos por módulo
    modules = AuditLog.objects.values('module').distinct()
    print("📦 Módulos com atividade:")
    for module in modules:
        if module['module']:
            count = AuditLog.objects.filter(module=module['module']).count()
            print(f"  - {module['module']}: {count} eventos")
    
    # Eventos por severidade
    print("\n⚠️ Eventos por severidade:")
    severities = AuditLog.objects.values('severity').distinct()
    severity_icons = {
        'LOW': '🟢',
        'MEDIUM': '🟡', 
        'HIGH': '🟠',
        'CRITICAL': '🔴'
    }
    for sev in severities:
        if sev['severity']:
            count = AuditLog.objects.filter(severity=sev['severity']).count()
            icon = severity_icons.get(sev['severity'], '⚪')
            print(f"  {icon} {sev['severity']}: {count} eventos")
    
    # IPs únicos
    unique_ips = SecurityEvent.objects.values_list('ip_address', flat=True).distinct()
    print(f"\n🌐 IPs únicos detectados: {len(unique_ips)}")
    for ip in unique_ips:
        if ip:
            events = SecurityEvent.objects.filter(ip_address=ip).count()
            print(f"  - {ip}: {events} eventos")
    
    # 6. Testar detecção de padrões
    print("\n6. Demonstrando detecção de padrões...")
    
    # Simular múltiplas tentativas do mesmo IP
    test_ip = '192.168.1.200'
    failed_attempts = SecurityEvent.objects.filter(
        event_type='FAILED_LOGIN',
        ip_address=test_ip
    ).count()
    
    if failed_attempts >= 1:
        print(f"🚨 Padrão suspeito detectado: {failed_attempts} tentativas de login do IP {test_ip}")
    
    # 7. Eventos recentes
    print("\n7. Eventos recentes (últimos 5):")
    recent_logs = AuditLog.objects.order_by('-timestamp')[:5]
    
    for log in recent_logs:
        timestamp = log.timestamp.strftime('%d/%m/%Y %H:%M:%S')
        severity_icon = severity_icons.get(log.severity, '⚪')
        print(f"  {severity_icon} {timestamp} - {log.event_type} - {log.description[:50]}...")
    
    # 8. Sumário final
    print("\n" + "=" * 50)
    print("✅ TESTE DO SISTEMA DE AUDITORIA CONCLUÍDO")
    print("\n📈 RESUMO FINAL:")
    print(f"  • {total_logs} logs de auditoria criados")
    print(f"  • {security_events} eventos de segurança registrados")
    print(f"  • {critical_events} eventos críticos detectados")
    print(f"  • {unresolved_security} eventos aguardando resolução")
    print(f"  • {len(unique_ips)} IPs únicos monitorados")
    
    print("\n🔧 PRÓXIMOS PASSOS:")
    print("  1. Configurar alertas por email")
    print("  2. Implementar dashboard de monitoramento")
    print("  3. Configurar limpeza automática de logs")
    print("  4. Integrar com sistema de tickets para eventos críticos")
    print("  5. Implementar relatórios de compliance")
    
    print("\n📚 COMANDOS ÚTEIS:")
    print("  python manage.py audit_stats --detailed")
    print("  python manage.py cleanup_audit_logs --dry-run")
    print("  curl http://localhost:8000/api/audit/logs/")
    print("  curl http://localhost:8000/api/audit/security-events/")
    
    print("\n🎉 Sistema de auditoria implementado com sucesso!")
    return True

if __name__ == "__main__":
    try:
        success = test_audit_system()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 
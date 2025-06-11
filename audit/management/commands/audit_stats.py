from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from audit.models import AuditLog, SecurityEvent, DataChangeHistory, AuditSettings


class Command(BaseCommand):
    help = 'Exibe estatísticas do sistema de auditoria'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Período em dias para as estatísticas (padrão: 30)'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Exibe estatísticas detalhadas'
        )

    def handle(self, *args, **options):
        days = options['days']
        detailed = options['detailed']
        
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        self.stdout.write(
            self.style.SUCCESS(f'=== ESTATÍSTICAS DE AUDITORIA ({days} dias) ===')
        )
        self.stdout.write(f'Período: {start_date.strftime("%d/%m/%Y %H:%M")} até {now.strftime("%d/%m/%Y %H:%M")}')
        self.stdout.write('')
        
        # Estatísticas básicas
        self._show_basic_stats(start_date, now)
        
        if detailed:
            self.stdout.write('')
            self._show_detailed_stats(start_date, now)
        
        # Configurações atuais
        self.stdout.write('')
        self._show_settings()
        
        # Alertas
        self.stdout.write('')
        self._show_alerts()
    
    def _show_basic_stats(self, start_date, end_date):
        """Exibe estatísticas básicas"""
        # Total de logs
        total_logs = AuditLog.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).count()
        
        # Eventos de segurança
        security_events = SecurityEvent.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).count()
        
        unresolved_security = SecurityEvent.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date,
            resolved=False
        ).count()
        
        # Mudanças de dados
        data_changes = DataChangeHistory.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).count()
        
        self.stdout.write('📊 RESUMO GERAL:')
        self.stdout.write(f'  Total de Logs: {total_logs:,}')
        self.stdout.write(f'  Eventos de Segurança: {security_events:,}')
        self.stdout.write(f'  Eventos Não Resolvidos: {unresolved_security:,}')
        self.stdout.write(f'  Mudanças de Dados: {data_changes:,}')
    
    def _show_detailed_stats(self, start_date, end_date):
        """Exibe estatísticas detalhadas"""
        self.stdout.write('📈 ESTATÍSTICAS DETALHADAS:')
        
        # Eventos por tipo
        self.stdout.write('\n🔍 Eventos por Tipo:')
        event_types = AuditLog.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for event in event_types:
            self.stdout.write(f'  {event["event_type"]}: {event["count"]:,}')
        
        # Eventos por severidade
        self.stdout.write('\n⚠️ Eventos por Severidade:')
        severities = AuditLog.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).values('severity').annotate(
            count=Count('id')
        ).order_by('-count')
        
        severity_icons = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }
        
        for severity in severities:
            icon = severity_icons.get(severity['severity'], '⚪')
            self.stdout.write(f'  {icon} {severity["severity"]}: {severity["count"]:,}')
        
        # Top usuários
        self.stdout.write('\n👥 Top 10 Usuários Mais Ativos:')
        top_users = AuditLog.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date,
            user__isnull=False
        ).values('user__username').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        for i, user in enumerate(top_users, 1):
            self.stdout.write(f'  {i:2d}. {user["user__username"]}: {user["count"]:,}')
        
        # Top IPs
        self.stdout.write('\n🌐 Top 10 Endereços IP:')
        top_ips = AuditLog.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date,
            ip_address__isnull=False
        ).values('ip_address').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        for i, ip in enumerate(top_ips, 1):
            self.stdout.write(f'  {i:2d}. {ip["ip_address"]}: {ip["count"]:,}')
        
        # Módulos mais ativos
        self.stdout.write('\n📦 Módulos Mais Ativos:')
        modules = AuditLog.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date,
            module__isnull=False
        ).values('module').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for module in modules:
            self.stdout.write(f'  {module["module"]}: {module["count"]:,}')
        
        # Eventos de segurança por tipo
        self.stdout.write('\n🔒 Eventos de Segurança por Tipo:')
        security_types = SecurityEvent.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for event in security_types:
            self.stdout.write(f'  {event["event_type"]}: {event["count"]:,}')
    
    def _show_settings(self):
        """Exibe configurações atuais"""
        settings = AuditSettings.get_settings()
        
        self.stdout.write('⚙️ CONFIGURAÇÕES ATUAIS:')
        self.stdout.write(f'  Retenção de Logs: {settings.retention_days} dias')
        self.stdout.write(f'  Alertas por Email: {"✅ Ativo" if settings.enable_email_alerts else "❌ Inativo"}')
        if settings.enable_email_alerts and settings.alert_email:
            self.stdout.write(f'  Email de Alertas: {settings.alert_email}')
        self.stdout.write(f'  Monitor de Logins Falhados: {"✅ Ativo" if settings.monitor_failed_logins else "❌ Inativo"}')
        if settings.monitor_failed_logins:
            self.stdout.write(f'  Máx. Tentativas de Login: {settings.max_failed_logins}')
        self.stdout.write(f'  Monitor de Transações: {"✅ Ativo" if settings.monitor_high_value_transactions else "❌ Inativo"}')
        if settings.monitor_high_value_transactions:
            self.stdout.write(f'  Valor Alto: ${settings.high_value_threshold:,}')
        self.stdout.write(f'  Log de Operações de Leitura: {"✅ Ativo" if settings.log_read_operations else "❌ Inativo"}')
        self.stdout.write(f'  Log de Chamadas API: {"✅ Ativo" if settings.log_api_calls else "❌ Inativo"}')
    
    def _show_alerts(self):
        """Exibe alertas importantes"""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        alerts = []
        
        # Eventos críticos nas últimas 24h
        critical_events = AuditLog.objects.filter(
            timestamp__gte=last_24h,
            severity='CRITICAL'
        ).count()
        
        if critical_events > 0:
            alerts.append(f'🔴 {critical_events} eventos críticos nas últimas 24h')
        
        # Eventos de segurança não resolvidos
        unresolved_security = SecurityEvent.objects.filter(resolved=False).count()
        if unresolved_security > 0:
            alerts.append(f'🔒 {unresolved_security} eventos de segurança não resolvidos')
        
        # Tentativas de força bruta
        brute_force = SecurityEvent.objects.filter(
            timestamp__gte=last_24h,
            event_type='BRUTE_FORCE'
        ).count()
        
        if brute_force > 0:
            alerts.append(f'⚠️ {brute_force} tentativas de força bruta nas últimas 24h')
        
        # Logs antigos para limpeza
        settings = AuditSettings.get_settings()
        if settings.retention_days > 0:
            cutoff_date = now - timedelta(days=settings.retention_days)
            old_logs = AuditLog.objects.filter(timestamp__lt=cutoff_date).count()
            if old_logs > 1000:
                alerts.append(f'🗂️ {old_logs:,} logs antigos precisam ser arquivados')
        
        # Exibir alertas
        if alerts:
            self.stdout.write('🚨 ALERTAS:')
            for alert in alerts:
                self.stdout.write(f'  {alert}')
        else:
            self.stdout.write('✅ Nenhum alerta ativo')
        
        # Sugestões
        self.stdout.write('')
        self.stdout.write('💡 SUGESTÕES:')
        if unresolved_security > 0:
            self.stdout.write('  • Revisar e resolver eventos de segurança pendentes')
        if critical_events > 5:
            self.stdout.write('  • Investigar eventos críticos recentes')
        if settings.retention_days > 0:
            cutoff_date = now - timedelta(days=settings.retention_days)
            old_logs = AuditLog.objects.filter(timestamp__lt=cutoff_date).count()
            if old_logs > 1000:
                self.stdout.write(f'  • Executar: python manage.py cleanup_audit_logs')
        
        self.stdout.write('  • Configurar alertas por email se ainda não estão ativos')
        self.stdout.write('  • Revisar logs de alto valor regularmente') 
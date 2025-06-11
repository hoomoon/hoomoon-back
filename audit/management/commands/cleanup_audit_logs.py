from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from audit.models import AuditLog, SecurityEvent, DataChangeHistory, AuditSettings


class Command(BaseCommand):
    help = 'Remove logs de auditoria antigos baseado na política de retenção'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            help='Número de dias para manter os logs (sobrescreve configuração)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria deletado sem executar'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation'
        )

    def handle(self, *args, **options):
        # Obter configurações de retenção
        settings = AuditSettings.get_settings()
        retention_days = options.get('days') or settings.retention_days
        
        if retention_days <= 0:
            self.stdout.write(
                self.style.WARNING('Política de retenção desabilitada (retention_days <= 0)')
            )
            return
        
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        # Contar logs a serem removidos
        audit_logs_count = AuditLog.objects.filter(timestamp__lt=cutoff_date).count()
        security_events_count = SecurityEvent.objects.filter(timestamp__lt=cutoff_date).count()
        data_changes_count = DataChangeHistory.objects.filter(timestamp__lt=cutoff_date).count()
        
        total_count = audit_logs_count + security_events_count + data_changes_count
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS('Nenhum log antigo encontrado para remoção')
            )
            return
        
        self.stdout.write(f'Logs a serem removidos (anteriores a {cutoff_date.strftime("%d/%m/%Y %H:%M:%S")}):')
        self.stdout.write(f'  - Logs de Auditoria: {audit_logs_count}')
        self.stdout.write(f'  - Eventos de Segurança: {security_events_count}')
        self.stdout.write(f'  - Histórico de Mudanças: {data_changes_count}')
        self.stdout.write(f'  - Total: {total_count}')
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN - Nenhum log foi removido')
            )
            return
        
        # Confirmação
        if not options['force']:
            confirm = input('\nDeseja continuar com a remoção? (sim/não): ')
            if confirm.lower() not in ['sim', 's', 'yes', 'y']:
                self.stdout.write('Operação cancelada')
                return
        
        # Remover logs
        deleted_counts = {}
        
        # DataChangeHistory primeiro (tem FK para AuditLog)
        if data_changes_count > 0:
            deleted_count, _ = DataChangeHistory.objects.filter(timestamp__lt=cutoff_date).delete()
            deleted_counts['DataChangeHistory'] = deleted_count
            self.stdout.write(f'Removidos {deleted_count} registros de histórico de mudanças')
        
        # AuditLog
        if audit_logs_count > 0:
            deleted_count, _ = AuditLog.objects.filter(timestamp__lt=cutoff_date).delete()
            deleted_counts['AuditLog'] = deleted_count
            self.stdout.write(f'Removidos {deleted_count} logs de auditoria')
        
        # SecurityEvent
        if security_events_count > 0:
            deleted_count, _ = SecurityEvent.objects.filter(timestamp__lt=cutoff_date).delete()
            deleted_counts['SecurityEvent'] = deleted_count
            self.stdout.write(f'Removidos {deleted_count} eventos de segurança')
        
        total_deleted = sum(deleted_counts.values())
        
        self.stdout.write(
            self.style.SUCCESS(f'Limpeza concluída! Total de registros removidos: {total_deleted}')
        )
        
        # Log da operação de limpeza
        from audit.utils import AuditLogger
        from audit.models import AuditEventType, AuditSeverity
        
        AuditLogger.log_event(
            event_type=AuditEventType.CONFIG_CHANGE,
            description=f'Limpeza automática de logs: {total_deleted} registros removidos',
            severity=AuditSeverity.MEDIUM,
            details={
                'retention_days': retention_days,
                'cutoff_date': cutoff_date.isoformat(),
                'deleted_counts': deleted_counts,
                'total_deleted': total_deleted
            },
            module='audit_cleanup'
        ) 
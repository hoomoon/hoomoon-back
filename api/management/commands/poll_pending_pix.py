# api/management/commands/poll_pending_pix.py
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.conf import settings # Para acessar API keys, etc.

# Supondo que ConnectPayService está em api/connectpay_service.py
# Ajuste o import se estiver em outro local.
from api.connectpay_service import ConnectPayService 
from api.models import Deposit, Investment, User # Seus modelos

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Consulta a API da ConnectPay para verificar o status de depósitos PIX pendentes e os atualiza.'

    def handle(self, *args, **options):
        self.stdout.write(f"[{timezone.now()}] Iniciando verificação de depósitos PIX pendentes...")

        # Busca depósitos PIX que estão PENDING e têm um ID de transação da ConnectPay
        # Adicionar outros status se houver estados intermediários antes de PENDING que precisam ser checados
        pending_deposits = Deposit.objects.filter(
            method='PIX', 
            status='PENDING', 
            connectpay_transaction_id__isnull=False
        ).select_related('user', 'plan') # Otimiza buscas futuras

        if not pending_deposits.exists():
            self.stdout.write("Nenhum depósito PIX pendente com ID da ConnectPay encontrado para verificação.")
            return

        connectpay_service = ConnectPayService()
        successful_updates = 0
        failed_updates = 0
        still_pending = 0

        for deposit in pending_deposits:
            self.stdout.write(f"Verificando Depósito ID: {deposit.id}, ConnectPay TXN ID: {deposit.connectpay_transaction_id}")

            try:
                with transaction.atomic(): # Garante atomicidade para cada depósito
                    # Re-fetch e lock dentro da transação para evitar race conditions se rodar em paralelo
                    d_to_update = Deposit.objects.select_for_update().get(pk=deposit.id)

                    # Segurança extra: verifica se o status ainda é PENDING antes de consultar
                    if d_to_update.status != 'PENDING':
                        self.stdout.write(f"Depósito ID: {d_to_update.id} não está mais PENDING (status atual: {d_to_update.status}). Pulando.")
                        continue

                    api_response, error_msg = connectpay_service.get_transaction_status(
                        d_to_update.connectpay_transaction_id
                    )

                    if error_msg or not api_response:
                        logger.error(f"Erro ao consultar status do Depósito ID {d_to_update.id} "
                                     f"(ConnectPay TXN ID: {d_to_update.connectpay_transaction_id}): {error_msg}")
                        # Decidir se quer marcar como falha ou tentar depois. Por ora, apenas loga.
                        continue

                    connectpay_status = api_response.get('status')
                    
                    logger.info(f"Depósito ID: {d_to_update.id}, ConnectPay Status: {connectpay_status}")

                    if connectpay_status == "AUTHORIZED":
                        d_to_update.status = 'CONFIRMED'
                        # Opcional: Salvar mais dados da resposta da API no depósito se necessário
                        # d_to_update.gateway_response_payload = api_response # Exemplo
                        d_to_update.save(update_fields=['status', 'updated_at']) # Adicionar 'gateway_response_payload' se usado

                        user_to_update = d_to_update.user # User já carregado com select_related
                        user_to_update.balance += d_to_update.amount
                        user_to_update.save(update_fields=['balance'])

                        self.stdout.write(self.style.SUCCESS(
                            f"Depósito ID: {d_to_update.id} CONFIRMADO. Saldo do usuário {user_to_update.username} atualizado."
                        ))
                        successful_updates += 1

                        # Criar/Ativar Investimento
                        if d_to_update.plan:
                            if not Investment.objects.filter(deposit_source=d_to_update).exists():
                                inv = Investment.objects.create(
                                    user=user_to_update,
                                    plan=d_to_update.plan,
                                    amount=d_to_update.amount,
                                    deposit_source=d_to_update,
                                    status='ACTIVE'
                                )
                                self.stdout.write(self.style.SUCCESS(
                                    f"Investimento {inv.code} criado e ativado para Depósito ID: {d_to_update.id}"
                                ))
                            else:
                                self.stdout.write(f"Investimento para Depósito ID: {d_to_update.id} já existe.")
                        else:
                            self.stdout.write(f"Depósito ID: {d_to_update.id} não tem plano associado. Nenhum investimento criado.")

                    elif connectpay_status == "FAILED": # Ou outros status de falha da ConnectPay
                        d_to_update.status = 'FAILED'
                        d_to_update.save(update_fields=['status', 'updated_at'])
                        self.stdout.write(self.style.ERROR(
                            f"Depósito ID: {d_to_update.id} FALHOU na ConnectPay."
                        ))
                        failed_updates += 1

                    elif connectpay_status == "PENDING":
                         self.stdout.write(f"Depósito ID: {d_to_update.id} ainda está PENDING na ConnectPay.")
                         still_pending +=1
                    else:
                        # Outros status (CHARGEBACK, IN_DISPUTE) podem precisar de tratamento específico
                        logger.info(f"Depósito ID: {d_to_update.id} com status ConnectPay não tratado: {connectpay_status}")
                        # Poderia atualizar o status do depósito para algo como 'NEEDS_REVIEW'

            except Deposit.DoesNotExist: # Caso o depósito tenha sido deletado entre a busca inicial e o processamento
                logger.warning(f"Depósito ID: {deposit.id} não encontrado durante o processamento (possivelmente deletado).")
            except Exception as e:
                logger.error(f"Erro inesperado ao processar Depósito ID {deposit.id}: {e}", exc_info=True)
                # Considerar enviar um alerta para administradores em caso de erros inesperados

        self.stdout.write(f"Verificação concluída: {successful_updates} confirmado(s), "
                          f"{failed_updates} falhou(s), {still_pending} ainda pendente(s).")
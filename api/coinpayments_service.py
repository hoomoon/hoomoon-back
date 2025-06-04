# api/coinpayments_service.py
import logging
from coinpayments import CoinPaymentsAPI # type: ignore
from django.conf import settings # type: ignore

logger = logging.getLogger(__name__)

class CoinPaymentsService:
    def __init__(self):
        self.client = CoinPaymentsAPI(
            public_key=settings.COINPAYMENTS_PUBLIC_KEY,
            private_key=settings.COINPAYMENTS_PRIVATE_KEY
        )

    def create_transaction(self, amount: float, user_email: str, ipn_url: str, deposit_id: int):
        try:
            params = {
                'amount': amount,
                'currency1': 'USD',
                'currency2': 'USDT.BEP20',
                'buyer_email': user_email,
                'ipn_url': ipn_url,
                'custom': str(deposit_id),
            }
            
            logger.debug(f"Criando transação na CoinPayments com params: {params}") # Exemplo de log DEBUG
            transaction = self.client.create_transaction(**params)
            
            if transaction.get('error') == 'ok':
                logger.info(f"Transação CoinPayments criada com sucesso para deposit_id {deposit_id}: {transaction['result']['txn_id']}") # Exemplo de log INFO
                return transaction
            else:
                # Usamos logger.error para erros
                logger.error(f"Erro da API CoinPayments ao criar transação para deposit_id {deposit_id}: {transaction.get('error')}") 
                return transaction # Retornamos para a view tratar a resposta ao usuário

        except Exception as e:
            # exc_info=True adiciona o traceback completo ao log
            logger.error(f"Exceção ao criar transação na CoinPayments para deposit_id {deposit_id}: {e}", exc_info=True) 
            return None

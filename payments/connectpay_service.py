# api/connectpay_service.py
import requests
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ConnectPayService:
    def __init__(self):
        self.base_url = settings.CONNECTPAY_BASE_URL
        self.api_secret = settings.CONNECTPAY_API_SECRET
        self.headers = {
            'api-secret': self.api_secret,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def create_pix_transaction(self, external_id: str, total_amount: float, webhook_url: str, 
                               items: list, customer_info: dict, client_ip: str):
        """
        Cria uma nova transação PIX na ConnectPay.
        """
        if not self.api_secret:
            logger.error("API Secret da ConnectPay não configurado.")
            return None, "API Secret não configurado."

        endpoint = f"{self.base_url}/v1/transactions"
        payload = {
            "external_id": external_id,
            "total_amount": total_amount,
            "payment_method": "PIX",
            "webhook_url": webhook_url,
            "items": items,
            "customer": customer_info,
            "ip": client_ip,
        }
        
        logger.debug(f"ConnectPay - Criando transação PIX. Endpoint: {endpoint}, Payload: {json.dumps(payload)}")

        try:
            response = requests.post(endpoint, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            
            response_data = response.json()
            logger.info(f"ConnectPay - Transação PIX criada com sucesso: {response_data.get('id')}")
            return response_data, None
            
        except requests.exceptions.HTTPError as http_err:
            error_content = ""
            try:
                error_content = response.json()
            except ValueError:
                error_content = response.text
            logger.error(f"ConnectPay - Erro HTTP ao criar transação PIX: {http_err}. Resposta: {error_content}")
            return None, f"Erro HTTP: {http_err} - {error_content}"
        except requests.exceptions.RequestException as req_err:
            logger.error(f"ConnectPay - Erro de requisição ao criar transação PIX: {req_err}")
            return None, f"Erro de Requisição: {req_err}"
        except Exception as e:
            logger.error(f"ConnectPay - Erro inesperado ao criar transação PIX: {e}", exc_info=True)
            return None, f"Erro inesperado: {str(e)}"

    def get_transaction_status(self, connectpay_transaction_id: str):
        """
        Consulta o status de uma transação existente na ConnectPay.
        """
        if not self.api_secret:
            logger.error("API Secret da ConnectPay não configurado.")
            return None, "API Secret não configurado."

        endpoint = f"{self.base_url}/v1/transactions/{connectpay_transaction_id}"
        logger.debug(f"ConnectPay - Consultando transação. Endpoint: {endpoint}")

        try:
            response = requests.get(endpoint, headers=self.headers, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"ConnectPay - Status da transação {connectpay_transaction_id}: {response_data.get('status')}")
            return response_data, None
            
        except requests.exceptions.HTTPError as http_err:
            error_content = ""
            try:
                error_content = response.json()
            except ValueError:
                error_content = response.text
            logger.error(f"ConnectPay - Erro HTTP ao consultar transação: {http_err}. Resposta: {error_content}")
            return None, f"Erro HTTP: {http_err} - {error_content}"
        except requests.exceptions.RequestException as req_err:
            logger.error(f"ConnectPay - Erro de requisição ao consultar transação: {req_err}")
            return None, f"Erro de Requisição: {req_err}"
        except Exception as e:
            logger.error(f"ConnectPay - Erro inesperado ao consultar transação: {e}", exc_info=True)
            return None, f"Erro inesperado: {str(e)}"
import hmac
import hashlib
from urllib.parse import urlencode

# 1. Defina o seu IPN Secret (o mesmo do seu settings.py e da CoinPayments)
# SUBSTITUA COM O SEU IPN SECRET REAL PARA O TESTE
ipn_secret = "1689ed8041c41f090dceccc5636fe0c25fa3c00ce55b387c831d5b3104b55898" 

# 2. Defina os dados do formulário (payload) que você enviará no corpo da requisição POST.
# Estes devem simular os dados que a CoinPayments envia.
# Consulte a documentação da CoinPayments para todos os campos possíveis.
# IMPORTANTE: O campo 'custom' deve ser o ID do objeto Deposit que você quer "confirmar".
form_data = {
    'merchant': "402175dd7d663a8f57e4c483b6b9f6ed", # O mesmo do settings.COINPAYMENTS_MERCHANT_ID
    'custom': "14", # Ex: '12' (o ID do Deposit que você criou via API e está PENDING)
    'status': "100", # Status de pagamento completo e confirmado pela CoinPayments
    'status_text': "Payment Complete",
    'txn_id': "CP_TEST_TXN_ID12345", # Um ID de transação da CoinPayments simulado
    'currency1': "USD", # Moeda do valor original do item/depósito
    'currency2': "USDT.BEP20", # Moeda do pagamento efetivamente feito
    'amount1': "150.00", # Valor na currency1 (ex: o valor do depósito que você iniciou)
    'amount2': "150.00", # Valor efetivamente pago na currency2
    # Adicione quaisquer outros campos que sua CoinPaymentsIPNView possa processar
    # ou que sejam tipicamente enviados pela CoinPayments, como 'ipn_type', 'ipn_mode', etc.
    # Por exemplo:
    'ipn_version': '1.0',
    'ipn_type': 'api', # ou 'simple', 'button', etc., dependendo da origem da transação
    'ipn_mode': 'hmac', 
    # 'buyer_name': 'Nome do Comprador Teste', # (opcional, se enviado pela CP)
    # 'email': 'email_do_comprador@teste.com' # (opcional, se enviado pela CP)
}

# 3. Codifique os dados do formulário para o formato application/x-www-form-urlencoded
# A CoinPayments envia os dados neste formato, e o HMAC é calculado sobre esta string.
raw_post_data = urlencode(form_data)

print(f"Dados do Formulário Codificados (raw_post_data para o corpo da requisição):\n{raw_post_data}\n")

# 4. Gere a assinatura HMAC
# Ela deve ser idêntica à forma como sua view calcula para validação.
generated_hmac = hmac.new(
    ipn_secret.encode('utf-8'),
    raw_post_data.encode('utf-8'),
    hashlib.sha512
).hexdigest()

print(f"HMAC Gerado (para o header 'Hmac'):\n{generated_hmac}")
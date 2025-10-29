import requests
import logging
from django.conf import settings
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class AsaasService:
    """Serviço para integração com a API do Asaas"""
    
    def __init__(self):
        self.api_key = settings.ASAAS_API_KEY
        self.base_url = settings.ASAAS_API_URL
        self.headers = {
            'Content-Type': 'application/json',
            'access_token': self.api_key
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Fazer requisição à API do Asaas"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Método HTTP inválido: {method}")
            
            response.raise_for_status()
            
            # Asaas retorna 200 para sucesso
            if response.status_code in [200, 201]:
                return response.json()
            
            logger.warning(f"Asaas response status {response.status_code}: {response.text}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao fazer requisição para Asaas: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
    
    def create_customer(self, customer_data: Dict) -> Optional[Dict]:
        """
        Criar cliente no Asaas
        
        Args:
            customer_data: Dict com dados do cliente
                - name: Nome completo
                - email: Email
                - cpfCnpj: CPF ou CNPJ
                - phone: Telefone (apenas números)
                - postalCode: CEP
                - address: Endereço
                - addressNumber: Número
                - complement: Complemento (opcional)
                - province: Bairro
                - city: Cidade
                - state: Estado (UF)
        
        Returns:
            Dict com dados do cliente criado ou None em caso de erro
        """
        # Verificar se cliente já existe pelo CPF/CNPJ
        existing = self._make_request('GET', '/customers', {'cpfCnpj': customer_data['cpfCnpj']})
        
        if existing and existing.get('data'):
            logger.info(f"Cliente já existe no Asaas: {customer_data['cpfCnpj']}")
            return existing['data'][0]
        
        # Criar novo cliente
        logger.info(f"Criando cliente no Asaas: {customer_data['email']}")
        result = self._make_request('POST', '/customers', customer_data)
        
        if result:
            logger.info(f"Cliente criado com sucesso: {result.get('id')}")
        
        return result
    
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Buscar cliente por ID"""
        return self._make_request('GET', f'/customers/{customer_id}')
    
    def update_customer(self, customer_id: str, customer_data: Dict) -> Optional[Dict]:
        """Atualizar dados do cliente"""
        return self._make_request('PUT', f'/customers/{customer_id}', customer_data)
    
    def create_subscription(self, subscription_data: Dict) -> Optional[Dict]:
        """
        Criar assinatura recorrente no Asaas
        
        Args:
            subscription_data: Dict com dados da assinatura
                - customer: ID do cliente no Asaas
                - billingType: BOLETO, CREDIT_CARD, PIX, etc
                - value: Valor da cobrança
                - nextDueDate: Data do primeiro vencimento (YYYY-MM-DD)
                - cycle: WEEKLY, BIWEEKLY, MONTHLY, QUARTERLY, SEMIANNUALLY, YEARLY
                - description: Descrição da assinatura
                - endDate: Data de término (opcional)
        
        Returns:
            Dict com dados da assinatura criada ou None em caso de erro
        """
        logger.info(f"Criando assinatura no Asaas para cliente: {subscription_data['customer']}")
        result = self._make_request('POST', '/subscriptions', subscription_data)
        
        if result:
            logger.info(f"Assinatura criada com sucesso: {result.get('id')}")
        
        return result
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict]:
        """Buscar assinatura por ID"""
        return self._make_request('GET', f'/subscriptions/{subscription_id}')
    
    def update_subscription(self, subscription_id: str, subscription_data: Dict) -> Optional[Dict]:
        """Atualizar assinatura"""
        return self._make_request('PUT', f'/subscriptions/{subscription_id}', subscription_data)
    
    def cancel_subscription(self, subscription_id: str) -> Optional[Dict]:
        """Cancelar assinatura"""
        logger.info(f"Cancelando assinatura no Asaas: {subscription_id}")
        return self._make_request('DELETE', f'/subscriptions/{subscription_id}')
    
    def get_payment(self, payment_id: str) -> Optional[Dict]:
        """Buscar cobrança por ID"""
        return self._make_request('GET', f'/payments/{payment_id}')
    
    def list_payments(self, filters: Optional[Dict] = None) -> Optional[Dict]:
        """Listar cobranças"""
        return self._make_request('GET', '/payments', filters)
    
    def get_payment_status(self, payment_id: str) -> Optional[str]:
        """
        Buscar status de uma cobrança
        
        Returns:
            Status: PENDING, RECEIVED, CONFIRMED, OVERDUE, REFUNDED, RECEIVED_IN_CASH, REFUND_REQUESTED, CHARGEBACK_REQUESTED, CHARGEBACK_DISPUTE, AWAITING_CHARGEBACK_REVERSAL, DUNNING_REQUESTED, DUNNING_RECEIVED, AWAITING_RISK_ANALYSIS
        """
        payment = self.get_payment(payment_id)
        return payment.get('status') if payment else None
    
    def refund_payment(self, payment_id: str) -> Optional[Dict]:
        """Estornar pagamento"""
        logger.info(f"Estornando pagamento no Asaas: {payment_id}")
        return self._make_request('POST', f'/payments/{payment_id}/refund')
    
    def generate_pix_qrcode(self, payment_id: str) -> Optional[Dict]:
        """Gerar QR Code PIX para pagamento"""
        result = self._make_request('GET', f'/payments/{payment_id}/pixQrCode')
        
        if result:
            logger.info(f"QR Code PIX gerado para pagamento: {payment_id}")
        
        return result
    
    def get_subscription_invoices(self, subscription_id: str) -> Optional[Dict]:
        """Listar faturas de uma assinatura"""
        return self._make_request('GET', f'/subscriptions/{subscription_id}/payments')
    
    def create_webhook(self, webhook_url: str, events: list) -> Optional[Dict]:
        """
        Configurar webhook no Asaas
        
        Args:
            webhook_url: URL que receberá os webhooks
            events: Lista de eventos, ex: ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED']
        
        Returns:
            Dict com dados do webhook criado
        """
        data = {
            'name': 'ChatbotsImas Webhook',
            'url': webhook_url,
            'email': settings.ADMIN_EMAIL,
            'enabled': True,
            'interrupted': False,
            'authToken': settings.ASAAS_WEBHOOK_TOKEN,
            'events': events
        }
        
        logger.info(f"Criando webhook no Asaas: {webhook_url}")
        return self._make_request('POST', '/webhooks', data)
    
    def list_webhooks(self) -> Optional[Dict]:
        """Listar webhooks configurados"""
        return self._make_request('GET', '/webhooks')
    
    def delete_webhook(self, webhook_id: str) -> Optional[Dict]:
        """Deletar webhook"""
        return self._make_request('DELETE', f'/webhooks/{webhook_id}')

    def create_payment_link(self, customer_id: str, value: float, description: str, due_date: str = None) -> Optional[Dict]:
        """
        Criar link de pagamento único (para primeira cobrança)
        
        Args:
            customer_id: ID do cliente no Asaas
            value: Valor da cobrança
            description: Descrição
            due_date: Data de vencimento (YYYY-MM-DD)
        
        Returns:
            Dict com dados do pagamento incluindo invoiceUrl
        """
        from datetime import date, timedelta
        
        if not due_date:
            due_date = (date.today() + timedelta(days=1)).isoformat()
        
        data = {
            'customer': customer_id,
            'billingType': 'UNDEFINED',  # Permite escolher no checkout
            'value': value,
            'dueDate': due_date,
            'description': description,
            'externalReference': f'first_payment_{customer_id}',
        }
        
        logger.info(f"Criando cobrança avulsa para cliente: {customer_id}")
        result = self._make_request('POST', '/payments', data)
        
        if result:
            logger.info(f"Cobrança criada: {result.get('id')} - URL: {result.get('invoiceUrl')}")
        
        return result
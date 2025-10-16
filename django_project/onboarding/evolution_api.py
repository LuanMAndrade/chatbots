import os
import requests
import logging

logger = logging.getLogger(__name__)

def get_evolution_api_config():
    """Retorna a configuração da Evolution API"""
    return {
        'base_url': os.getenv('EVOLUTION_API_BASE_URL', 'http://evolution-api:8080'),
        'api_key': os.getenv('EVOLUTION_API_KEY', ''),
    }

# def get_whatsapp_contacts(username):
#     """
#     Busca os contatos do WhatsApp através da Evolution API
    
#     Args:
#         username: Nome do usuário para buscar a instância correspondente
    
#     Returns:
#         Lista de contatos ou None em caso de erro
#     """
#     try:
#         config = get_evolution_api_config()
        
#         # Nome da instância baseado no username
#         instance_name = f"bot_{username}"
        
#         # Tenta diferentes rotas da Evolution API v2
#         possible_routes = [
#             f"{config['base_url']}/chat/findContacts/{instance_name}",
#             f"{config['base_url']}/chat/fetchAllContacts/{instance_name}",
#             f"{config['base_url']}/contact/fetchAllContacts/{instance_name}",
#         ]
        
#         headers = {
#             'apikey': config['api_key'],
#             'Content-Type': 'application/json'
#         }
        
#         contacts = []
        
#         for url in possible_routes:
#             try:
#                 logger.info(f"Tentando buscar contatos em: {url}")
#                 response = requests.get(url, headers=headers, timeout=10)
                
#                 if response.status_code == 200:
#                     data = response.json()
#                     logger.info(f"Resposta recebida - Status: 200")
#                     logger.info(f"Tipo de resposta: {type(data)}")
                    
#                     # A resposta pode vir em diferentes formatos
#                     items = data
#                     if isinstance(data, dict):
#                         # Tenta diferentes chaves possíveis
#                         items = (data.get('contacts') or 
#                                 data.get('data') or 
#                                 data.get('response') or 
#                                 data.get('chats') or [])
                    
#                     if isinstance(items, list):
#                         for contact in items:
#                             # Filtra apenas contatos salvos (não grupos)
#                             contact_id = contact.get('id') or contact.get('remoteJid') or ''
                            
#                             # Ignora grupos (@g.us) e status (@broadcast)
#                             if contact_id and not contact_id.endswith('@g.us') and not contact_id.endswith('@broadcast'):
#                                 # Extrai informações do contato
#                                 name = (
#                                     contact.get('pushName') or 
#                                     contact.get('name') or 
#                                     contact.get('verifiedName') or
#                                     contact.get('notify') or
#                                     contact.get('displayName') or
#                                     contact_id.split('@')[0]
#                                 )
                                
#                                 phone = contact_id.split('@')[0]
                                
#                                 # Remove código do país 55 para exibição
#                                 display_phone = phone
#                                 if phone.startswith('55') and len(phone) > 11:
#                                     display_phone = phone[2:]
                                
#                                 contacts.append({
#                                     'id': contact_id,
#                                     'name': name,
#                                     'phone': display_phone
#                                 })
                        
#                         if contacts:
#                             logger.info(f"Encontrados {len(contacts)} contatos")
#                             # Ordena por nome
#                             contacts.sort(key=lambda x: x['name'].lower())
#                             return contacts
                
#                 logger.warning(f"Rota {url} retornou status {response.status_code}")
                
#             except requests.exceptions.RequestException as e:
#                 logger.warning(f"Erro na rota {url}: {e}")
#                 continue
        
#         # Se nenhuma rota funcionou, retorna lista vazia ao invés de None
#         logger.error(f"Não foi possível buscar contatos de nenhuma rota")
#         return []
            
#     except Exception as e:
#         logger.error(f"Erro ao processar contatos: {e}")
#         return []

def get_whatsapp_contacts(username):

def send_whatsapp_message(username, phone_number, message):
    """
    Envia uma mensagem via Evolution API
    
    Args:
        username: Nome do usuário
        phone_number: Número do telefone (formato: 5511999999999)
        message: Texto da mensagem
    
    Returns:
        True se enviado com sucesso, False caso contrário
    """
    try:
        config = get_evolution_api_config()
        instance_name = f"bot_{username}"
        
        url = f"{config['base_url']}/message/sendText/{instance_name}"
        
        headers = {
            'apikey': config['api_key'],
            'Content-Type': 'application/json'
        }
        
        # Remove caracteres não numéricos do telefone
        clean_phone = ''.join(filter(str.isdigit, phone_number))
        
        # Garante que tem o código do país (55 para Brasil)
        if not clean_phone.startswith('55') and len(clean_phone) == 11:
            clean_phone = '55' + clean_phone
        
        # Adiciona @s.whatsapp.net se necessário
        if '@' not in clean_phone:
            clean_phone = f"{clean_phone}@s.whatsapp.net"
        
        payload = {
            "number": clean_phone,
            "text": message
        }
        
        logger.info(f"Enviando mensagem para {clean_phone}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"Mensagem enviada com sucesso para {phone_number}")
            return True
        else:
            logger.error(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem via Evolution API: {e}")
        return False


if __name__ == "__main__":
    contatos = get_whatsapp_contacts('model')
    print(contatos)
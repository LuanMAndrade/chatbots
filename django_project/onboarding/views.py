from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.utils import timezone
from django.contrib import messages
from .models import AutomatedMessage, BotInfo
from . import langsmith_utils
from . import evolution_api
import psycopg2
import os
import subprocess
import sys
import logging
import calendar
import re
from .models import AdditionalFeature

logger = logging.getLogger(__name__)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.conf import settings
from .models import Plan, ClientSubscription, BotInstance, Invoice, PortRegistry
from .asaas_service import AsaasService
import json
import logging
from datetime import date, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


def landing_page(request):
    """Landing page pública com os planos"""
    plans = Plan.objects.filter(ativo=True).prefetch_related('funcionalidades')
    additional_features = AdditionalFeature.objects.filter(ativo=True)
    
    context = {
        'plans': plans,
        'additional_features': additional_features,
    }
    return render(request, 'onboarding/landing.html', context)


def checkout_view(request, plan_id):
    """Página de checkout"""
    plan = get_object_or_404(Plan, id=plan_id, ativo=True)
    
    # Pegar addons selecionados da URL
    addon_ids = request.GET.get('addons', '').split(',')
    selected_addons = []
    addons_total = Decimal('0.00')
    
    if addon_ids and addon_ids[0]:
        selected_addons = AdditionalFeature.objects.filter(
            id__in=addon_ids,
            ativo=True
        )
        addons_total = sum(addon.preco_mensal for addon in selected_addons)
    
    total_price = plan.preco_mensal + addons_total
    
    if request.method == 'POST':
        try:
            # Extrair dados do formulário
            customer_data = {
                'name': request.POST.get('name'),
                'email': request.POST.get('email'),
                'phone': request.POST.get('phone').replace('(', '').replace(')', '').replace('-', '').replace(' ', ''),
                'cpfCnpj': request.POST.get('cpfCnpj').replace('.', '').replace('-', '').replace('/', ''),
                'postalCode': request.POST.get('postalCode').replace('-', ''),
                'address': request.POST.get('address'),
                'addressNumber': request.POST.get('addressNumber'),
                'complement': request.POST.get('complement', ''),
                'province': request.POST.get('address'),
                'city': request.POST.get('city'),
                'state': request.POST.get('state'),
            }
            
            # Extrair e validar username e senha
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password')
            email = customer_data['email'].lower()
            cpf_cnpj = customer_data['cpfCnpj']
            name = customer_data['name']
            
            # Inicializar serviço Asaas ANTES das validações
            asaas = AsaasService()
            
            # ========================================
            # VALIDAÇÕES BACKEND (antes de criar qualquer coisa)
            # ========================================
            
            # Validar username (padrão seguro)
            import re
            if not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
                return JsonResponse({
                    'success': False,
                    'error': 'Nome de usuário inválido. Use apenas letras, números e underscore.'
                })
            
            # Verificar duplicidades no Django
            if User.objects.filter(username__iexact=username).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Nome de usuário já existe. Escolha outro.'
                })
            
            if User.objects.filter(email__iexact=email).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Email já cadastrado. Use outro ou faça login.'
                })
            
            # Verificar CPF no Asaas ANTES de criar
            existing_customer_check = asaas._make_request('GET', '/customers', {'cpfCnpj': cpf_cnpj})
            if existing_customer_check and existing_customer_check.get('data') and len(existing_customer_check['data']) > 0:
                return JsonResponse({
                    'success': False,
                    'error': 'CPF/CNPJ já cadastrado no sistema.'
                })
            
            # Verificar Nome no Asaas ANTES de criar (opcional, pode comentar se não quiser)
            existing_name_check = asaas._make_request('GET', '/customers', {'name': name})
            if existing_name_check and existing_name_check.get('data') and len(existing_name_check['data']) > 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Nome completo já cadastrado no sistema.'
                })
            
            # ========================================
            # AGORA SIM: CRIAR DADOS (todas validações passaram)
            # ========================================
            
            # Criar cliente no Asaas
            asaas_customer = asaas.create_customer(customer_data)
            
            if not asaas_customer:
                return JsonResponse({
                    'success': False,
                    'error': 'Erro ao criar cliente no Asaas'
                })
            
            # Criar assinatura no Asaas (para cobranças recorrentes futuras)
            subscription_data = {
                'customer': asaas_customer['id'],
                'billingType': 'UNDEFINED',
                'value': float(total_price),
                'nextDueDate': (date.today() + timedelta(days=30)).isoformat(),
                'cycle': 'MONTHLY',
                'description': f'Assinatura {plan.nome} - ChatbotsImas',
            }
            
            asaas_subscription = asaas.create_subscription(subscription_data)
            
            if not asaas_subscription:
                # Se falhar, tentar deletar o cliente criado
                asaas._make_request('DELETE', f'/customers/{asaas_customer["id"]}')
                return JsonResponse({
                    'success': False,
                    'error': 'Erro ao criar assinatura'
                })
            
            # Criar cobrança AVULSA para primeira mensalidade
            first_payment = asaas.create_payment_link(
                customer_id=asaas_customer['id'],
                value=float(total_price),
                description=f'Primeira mensalidade - {plan.nome}'
            )
            
            if not first_payment:
                # Se falhar, tentar deletar assinatura e cliente
                asaas._make_request('DELETE', f'/subscriptions/{asaas_subscription["id"]}')
                asaas._make_request('DELETE', f'/customers/{asaas_customer["id"]}')
                return JsonResponse({
                    'success': False,
                    'error': 'Erro ao gerar link de pagamento'
                })
            
            # Criar usuário Django
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=name.split()[0],
                last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
            )
            
            # Criar ClientSubscription
            subscription = ClientSubscription.objects.create(
                user=user,
                plano=plan,
                tokens_incluidos_no_plano=plan.tokens_incluidos,
                billing_day=date.today().day if date.today().day <= 28 else 28,
                data_inicio=date.today(),
                status='pending',
                payment_gateway_subscription_id=asaas_subscription['id'],
                payment_gateway_customer_id=asaas_customer['id'],
            )
            
            # Vincular addons
            if selected_addons:
                subscription.funcionalidades_extras.set(selected_addons)
            
            # Criar fatura vinculada ao pagamento avulso
            Invoice.objects.create(
                subscription=subscription,
                periodo_inicio=date.today(),
                periodo_fim=date.today() + timedelta(days=30),
                valor_plano=plan.preco_mensal,
                valor_total=total_price,
                data_vencimento=date.today() + timedelta(days=1),
                status='pending',
                payment_id=first_payment.get('id'),
                payment_url=first_payment.get('invoiceUrl', ''),
            )
            
            # Redirecionar para página de pagamento do Asaas
            payment_url = first_payment.get('invoiceUrl')
            
            if not payment_url:
                return JsonResponse({
                    'success': False,
                    'error': 'Link de pagamento não foi gerado'
                })
            
            return JsonResponse({
                'success': True,
                'redirect_url': payment_url
            })
            
        except Exception as e:
            logger.error(f"Erro no checkout: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    context = {
        'plan': plan,
        'selected_addons': selected_addons,
        'addons_total': addons_total,
        'total_price': total_price,
    }
    return render(request, 'onboarding/checkout.html', context)


def success_view(request):
    """Página de sucesso após CONFIRMAÇÃO de pagamento"""
    subscription_id = request.GET.get('subscription_id')
    subscription = get_object_or_404(ClientSubscription, id=subscription_id)
    
    # Verificar se realmente está ativa
    if subscription.status != 'active':
        # Se ainda não foi confirmada, redirecionar para pending
        return redirect(f'/payment-pending/?subscription_id={subscription.id}')
    
    context = {
        'subscription': subscription,
    }
    return render(request, 'onboarding/success.html', context)


def payment_pending_view(request):
    """Página para pagamentos pendentes (boleto/PIX)"""
    subscription_id = request.GET.get('subscription_id')
    subscription = get_object_or_404(ClientSubscription, id=subscription_id)
    
    # Buscar fatura mais recente
    invoice = subscription.invoices.filter(status='pending').order_by('-created_at').first()
    
    context = {
        'subscription': subscription,
        'invoice': invoice,
    }
    return render(request, 'onboarding/payment_pending.html', context)


@csrf_exempt
@require_POST
def asaas_webhook(request):
    """Webhook para receber notificações do Asaas"""
    try:
        # Verificar token
        webhook_token = request.headers.get('asaas-access-token')
        if webhook_token and hasattr(settings, 'ASAAS_WEBHOOK_TOKEN'):
            if webhook_token != settings.ASAAS_WEBHOOK_TOKEN:
                return HttpResponse('Unauthorized', status=401)
        
        # Parse do payload
        payload = json.loads(request.body)
        event = payload.get('event')
        payment_data = payload.get('payment', {})
        
        logger.info(f"Webhook recebido: {event} - Payment ID: {payment_data.get('id')}")
        
        if event in ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED']:
            # Pagamento confirmado
            payment_id = payment_data.get('id')
            
            # Buscar fatura
            invoice = Invoice.objects.filter(payment_id=payment_id).first()
            
            if invoice:
                # Marcar fatura como paga
                invoice.marcar_como_paga()
                
                # Ativar subscription
                subscription = invoice.subscription
                if subscription.status == 'pending':
                    subscription.status = 'active'
                    subscription.save()
                    
                    logger.info(f"✅ Subscription {subscription.id} ATIVADA - Pagamento confirmado!")
                    
                    # TODO: Criar bot automaticamente (Fase 3)
                    # create_bot_instance(subscription)
                    
                    # TODO: Enviar email de boas-vindas
        
        elif event == 'PAYMENT_OVERDUE':
            # Pagamento atrasado
            payment_id = payment_data.get('id')
            invoice = Invoice.objects.filter(payment_id=payment_id).first()
            
            if invoice:
                invoice.status = 'overdue'
                invoice.save()
                
                # Suspender subscription se múltiplas faturas vencidas
                subscription = invoice.subscription
                overdue_count = subscription.invoices.filter(status='overdue').count()
                
                if overdue_count >= 2:
                    subscription.status = 'suspended'
                    subscription.save()
                    logger.warning(f"⚠️ Subscription {subscription.id} SUSPENSA por inadimplência")
        
        elif event == 'PAYMENT_DELETED':
            # Pagamento cancelado
            payment_id = payment_data.get('id')
            invoice = Invoice.objects.filter(payment_id=payment_id).first()
            
            if invoice:
                invoice.status = 'cancelled'
                invoice.save()
        
        return HttpResponse('OK', status=200)
        
    except Exception as e:
        logger.error(f"❌ Erro no webhook: {str(e)}")
        return HttpResponse('Error', status=500)


@login_required
def my_subscription_view(request):
    """Página da assinatura do usuário logado"""
    try:
        subscription = request.user.subscription
    except ClientSubscription.DoesNotExist:
        return redirect('landing_page')
    
    # Buscar faturas
    invoices = subscription.invoices.order_by('-created_at')[:12]
    
    # Buscar bot
    bot = None
    try:
        bot = subscription.bot_instance
    except BotInstance.DoesNotExist:
        pass
    
    context = {
        'subscription': subscription,
        'invoices': invoices,
        'bot': bot,
    }
    return render(request, 'onboarding/my_subscription.html', context)


@login_required
def cancel_subscription_view(request):
    """Cancelar assinatura"""
    try:
        subscription = request.user.subscription
    except ClientSubscription.DoesNotExist:
        return redirect('landing_page')
    
    if request.method == 'POST':
        # Cancelar no Asaas
        asaas = AsaasService()
        asaas.cancel_subscription(subscription.payment_gateway_subscription_id)
        
        # Atualizar no banco
        subscription.status = 'cancelled'
        subscription.data_cancelamento = date.today()
        subscription.save()
        
        return redirect('my_subscription')
    
    context = {
        'subscription': subscription,
    }
    return render(request, 'onboarding/cancel_subscription.html', context)

# --- Views de Autenticação ---
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    """Faz logout do usuário"""
    logout(request)
    messages.success(request, 'Você saiu com sucesso!')
    return redirect('login')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Sua senha foi alterada com sucesso!')
            return redirect('profile')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'profile.html', {'form': form})

@login_required
def dashboard_view(request):
    # CORREÇÃO: Estatísticas - conta todas as pendentes
    pending_count = AutomatedMessage.objects.filter(
        user=request.user,
        status='pending'
    ).count()
    
    sent_count = AutomatedMessage.objects.filter(
        user=request.user,
        status='sent'
    ).count()
    
    try:
        bot_info = BotInfo.objects.get(user=request.user)
        has_bot_info = bool(bot_info.info_text)
    except BotInfo.DoesNotExist:
        has_bot_info = False
    has_bot_info= True
    
    context = {
        'pending_count': pending_count,
        'sent_count': sent_count,
        'has_bot_info': has_bot_info,
    }
    return render(request, 'dashboard.html', context)

@login_required
def add_info_view(request):
    try:
        bot_info = BotInfo.objects.get(user=request.user)
    except BotInfo.DoesNotExist:
        bot_info = None

    if request.method == 'POST':
        # Coleta todos os campos do formulário
        horarios_atendimento = request.POST.get('horarios_atendimento', '')
        endereco_atendimento = request.POST.get('endereco_atendimento', '')
        nome_profissional = request.POST.get('nome_profissional', '')
        profissao = request.POST.get('profissao', '')
        produtos_servicos_precos = request.POST.get('produtos_servicos_precos', '')
        informacoes_relevantes = request.POST.get('informacoes_relevantes', '')
        modo_atendimento = request.POST.get('modo_atendimento', '')
        
        # Atualiza ou cria o BotInfo com todos os campos
        BotInfo.objects.update_or_create(
            user=request.user,
            defaults={
                'horarios_atendimento': horarios_atendimento,
                'endereco_atendimento': endereco_atendimento,
                'nome_profissional': nome_profissional,
                'profissao': profissao,
                'produtos_servicos_precos': produtos_servicos_precos,
                'informacoes_relevantes': informacoes_relevantes,
                'modo_atendimento': modo_atendimento,
            }
        )
        
        try:
            username = request.user.username
            bot_project_path = f"/root/chatbots/bot_{username}"
            update_script_path = os.path.join(bot_project_path, "django_utils/update_info.py")

            if os.path.exists(update_script_path):
                python_executable = f"/root/chatbots/bot_{username}/venv/bin/python"
                if not os.path.exists(python_executable):
                    python_executable = sys.executable

                result = subprocess.run(
                    [python_executable, update_script_path, username],
                    capture_output=True,
                    text=True,
                    check=False
                )

                if result.returncode == 0:
                    messages.success(request, 'Informações salvas e bot atualizado com sucesso!')
                else:
                    error_log = result.stderr or "Ocorreu um erro desconhecido no script de atualização."
                    messages.error(request, f'Falha ao atualizar o bot. Erro: {error_log}')
            else:
                messages.warning(request, f'Script de atualização (update_info.py) não encontrado para o bot_{username}.')

        except Exception as e:
            messages.error(request, f'Ocorreu um erro ao executar o script de atualização: {e}')
        
        return redirect('dashboard')

    context = {
        'bot_info': bot_info
    }
    return render(request, 'add_info.html', context)
    
# --- Views de Mensagens Automáticas ---
@login_required
def auto_messages_dashboard_view(request):
    now = timezone.now()
    
    # CORREÇÃO: Mensagens pendentes - filtra APENAS por status
    # Agora mostra todas as pendentes, mesmo que já tenha passado da hora
    # (elas sumirão quando o agendador mudar o status)
    upcoming_messages = AutomatedMessage.objects.filter(
        user=request.user,
        status='pending'
    ).order_by('send_at')[:10]
    
    # Mensagens enviadas recentemente
    sent_messages = AutomatedMessage.objects.filter(
        user=request.user,
        status='sent'
    ).order_by('-sent_at')[:10]
    
    # Números únicos com mensagens agendadas
    scheduled_numbers = AutomatedMessage.objects.filter(
        user=request.user,
        status='pending'
    ).values('contact_name', 'phone_number').distinct()

    context = {
        'upcoming_messages': upcoming_messages,
        'sent_messages': sent_messages,
        'scheduled_numbers': scheduled_numbers,
    }
    return render(request, 'auto_messages_dashboard.html', context)

@login_required
def auto_messages_detail_view(request, phone_number):
    all_messages = AutomatedMessage.objects.filter(
        user=request.user,
        phone_number=phone_number
    ).order_by('-send_at')
    
    contact_name = all_messages.first().contact_name if all_messages.exists() else phone_number
    
    context = {
        'phone_number': phone_number,
        'contact_name': contact_name,
        'messages': all_messages,
    }
    return render(request, 'auto_messages_detail.html', context)

@login_required
def auto_messages_form_view(request, message_id=None):
    instance = None
    if message_id:
        instance = get_object_or_404(AutomatedMessage, id=message_id, user=request.user)

    # Busca contatos do WhatsApp
    whatsapp_contacts = evolution_api.get_whatsapp_contacts(request.user.username)
    
    if request.method == 'POST':
        source = request.POST.get('contact_source')
        
        if source == 'whatsapp':
            contact_id = request.POST.get('whatsapp_contact')
            if contact_id and whatsapp_contacts:
                selected_contact = next((c for c in whatsapp_contacts if c['id'] == contact_id), None)
                if selected_contact:
                    contact_name = selected_contact['name']
                    phone_number = selected_contact['phone']
                else:
                    messages.error(request, 'Contato não encontrado.')
                    return redirect('auto_messages_new')
            else:
                messages.error(request, 'Por favor, selecione um contato.')
                return redirect('auto_messages_new')
        else:
            contact_name = request.POST.get('contact_name')
            phone_number = request.POST.get('phone_number')
            phone_number = '55' + re.sub(r'\D', '', phone_number)
            
            if not contact_name or not phone_number:
                messages.error(request, 'Nome e número são obrigatórios.')
                return redirect('auto_messages_new')
        
        message = request.POST.get('message')
        send_at = request.POST.get('send_at')
        
        if instance:
            instance.contact_name = contact_name
            instance.phone_number = phone_number
            instance.message = message
            instance.send_at = send_at
            instance.save()
            messages.success(request, 'Mensagem atualizada com sucesso!')
        else:
            AutomatedMessage.objects.create(
                user=request.user,
                contact_name=contact_name,
                phone_number=phone_number,
                message=message,
                send_at=send_at
            )
            messages.success(request, 'Mensagem agendada com sucesso!')
        
        return redirect('auto_messages_dashboard')
    
    context = {
        'message_instance': instance,
        'whatsapp_contacts': whatsapp_contacts,
    }
    return render(request, 'auto_messages_form.html', context)

@login_required
def auto_messages_delete_view(request, message_id):
    message_to_delete = get_object_or_404(AutomatedMessage, id=message_id, user=request.user)
    
    if request.method == 'POST':
        message_to_delete.delete()
        messages.success(request, 'Mensagem excluída com sucesso!')
        return redirect('auto_messages_dashboard')
    
    return render(request, 'auto_messages_delete_confirm.html', {'message': message_to_delete})

# --- View de Consumo ---
@login_required
def consumo_view(request):
    # Determina o projeto baseado no username
    username = request.user.username
    selected_project = f'bot_{username}'
    
    # NOVO: Buscar configurações da subscription
    try:
        subscription = request.user.subscription
        billing_day = subscription.billing_day
        tokens_incluidos = subscription.tokens_incluidos_no_plano
    except:
        # Valores padrão se não tiver subscription
        billing_day = 18
        tokens_incluidos = 1000000
    
    available_months = langsmith_utils.get_available_months()
    selected_month_str = request.GET.get('month', available_months[0]['value'])
    
    year, month = map(int, selected_month_str.split('-'))
    start_time, end_time = langsmith_utils.get_month_period(
    year, 
    month, 
    billing_day=billing_day  # NOVO
)
    
    usage_data = {}
    daily_data = []
    error = None
    
    try:
        # Usa a função otimizada que faz apenas uma chamada ao LangSmith
        result = langsmith_utils.get_usage_data_optimized(
    selected_project, 
    start_time, 
    end_time,
    tokens_incluidos=tokens_incluidos  # NOVO
)
        usage_data = result['usage_data']
        daily_data = result['daily_data']
        
        # Adiciona informações do mês para o template
        usage_data['month_name'] = calendar.month_name[month]
        usage_data['year'] = year
    except Exception as e:
        error = f"Erro ao buscar dados do LangSmith: {e}"
        logger.error(error)
    
    context = {
        'selected_project': selected_project,
        'available_months': available_months,
        'selected_month': selected_month_str,
        'usage_data': usage_data,
        'daily_data': daily_data,
        'error': error,
    }
    return render(request, 'consumo.html', context)

@login_required
def clear_whatsapp_contacts_view(request):
    """View para limpar contatos do WhatsApp"""
    
    if request.method == 'POST':
        username = request.user.username
        instance_name = f"bot_{username}"
        
        try:
            conn = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD'),
                host='postgres',
                port='5432'
            )
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM public."Instance"
                    WHERE name = %s
                """, (instance_name,))
                
                result = cur.fetchone()
                
                if not result:
                    messages.error(request, 'Instância não encontrada.')
                    return redirect('auto_messages_dashboard')
                
                instance_id = result[0]
                
                cur.execute("""
                    SELECT COUNT(*) FROM public."Contact"
                    WHERE "instanceId" = %s
                """, (instance_id,))
                
                count = cur.fetchone()[0]
                
                if count == 0:
                    messages.info(request, 'Nenhum contato encontrado para deletar.')
                    return redirect('auto_messages_dashboard')
                
                cur.execute("""
                    DELETE FROM public."Contact"
                    WHERE "instanceId" = %s
                """, (instance_id,))
                
                conn.commit()
                
                messages.success(
                    request, 
                    f'✅ {count} contato(s) deletado(s) com sucesso!'
                )
                
        except Exception as e:
            messages.error(request, f'Erro ao deletar contatos: {e}')
        
        finally:
            if conn:
                conn.close()
        
        return redirect('auto_messages_dashboard')
    
    # GET - Mostra página de confirmação
    username = request.user.username
    instance_name = f"bot_{username}"
    
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host='postgres',
            port='5432'
        )
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) 
                FROM public."Contact" c
                JOIN public."Instance" i ON c."instanceId" = i.id
                WHERE i.name = %s
            """, (instance_name,))
            
            contact_count = cur.fetchone()[0]
    
    except Exception as e:
        contact_count = 0
        messages.error(request, f'Erro ao contar contatos: {e}')
    
    finally:
        if conn:
            conn.close()
    
    return render(request, 'clear_contacts_confirm.html', {
        'contact_count': contact_count
    })

def check_username_availability(request):
    """API para verificar se username está disponível"""
    username = request.GET.get('username', '').strip()
    
    if not username or len(username) < 3:
        return JsonResponse({'available': False, 'message': 'Username muito curto'})
    
    # Validar padrão (apenas letras, números e underscore)
    import re
    if not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
        return JsonResponse({'available': False, 'message': 'Use apenas letras, números e underscore'})
    
    # Verificar se já existe
    exists = User.objects.filter(username__iexact=username).exists()
    
    return JsonResponse({
        'available': not exists,
        'message': 'Já existe' if exists else 'Disponível'
    })


def check_email_availability(request):
    """API para verificar se email está disponível"""
    email = request.GET.get('email', '').strip().lower()
    
    if not email:
        return JsonResponse({'available': False})
    
    # Verificar se já existe
    exists = User.objects.filter(email__iexact=email).exists()
    
    return JsonResponse({'available': not exists})


def check_cpf_availability(request):
    """API para verificar se CPF/CNPJ está disponível"""
    cpf = request.GET.get('cpf', '').strip()
    
    if not cpf or len(cpf) < 11:
        return JsonResponse({'available': False})
    
    # Verificar no Asaas (clientes já cadastrados)
    asaas = AsaasService()
    existing = asaas._make_request('GET', '/customers', {'cpfCnpj': cpf})
    
    if existing and existing.get('data') and len(existing['data']) > 0:
        return JsonResponse({'available': False})
    
    return JsonResponse({'available': True})


def check_name_availability(request):
    """API para verificar se nome completo está disponível"""
    name = request.GET.get('name', '').strip()
    
    if not name or len(name) < 3:
        return JsonResponse({'available': False})
    
    # Verificar no Asaas (clientes já cadastrados)
    asaas = AsaasService()
    existing = asaas._make_request('GET', '/customers', {'name': name})
    
    if existing and existing.get('data') and len(existing['data']) > 0:
        return JsonResponse({'available': False})
    
    return JsonResponse({'available': True})
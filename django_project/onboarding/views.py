from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.utils import timezone
from django.contrib import messages
from .models import AutomatedMessage, BotInfo
from . import langsmith_utils
from . import evolution_api
import os
import subprocess
import sys
import logging
import calendar
import re

logger = logging.getLogger(__name__)

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
    
    available_months = langsmith_utils.get_available_months()
    selected_month_str = request.GET.get('month', available_months[0]['value'])
    
    year, month = map(int, selected_month_str.split('-'))
    start_time, end_time = langsmith_utils.get_month_period(year, month)
    
    usage_data = {}
    daily_data = []
    error = None
    
    try:
        # Usa a função otimizada que faz apenas uma chamada ao LangSmith
        result = langsmith_utils.get_usage_data_optimized(selected_project, start_time, end_time)
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
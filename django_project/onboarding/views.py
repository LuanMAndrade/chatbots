from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from .models import AutomatedMessage, BotInfo
import os
import subprocess
import sys
from django.contrib import messages
from . import langsmith_utils
import logging
import calendar

# --- Views de Autenticação e Informações (sem alterações) ---
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
def dashboard_view(request):
    return render(request, 'dashboard.html')

# Adicione estas importações no início do arquivo views.py


@login_required
def add_info_view(request):
    try:
        bot_info = BotInfo.objects.get(user=request.user)
    except BotInfo.DoesNotExist:
        bot_info = None

    if request.method == 'POST':
        info_text = request.POST.get('info_text')
        # 1. Salva no banco de dados
        BotInfo.objects.update_or_create(
            user=request.user,
            defaults={'info_text': info_text}
        )
        
        # 2. Executa o gatilho e captura os logs
        try:
            username = request.user.username
            bot_project_path = f"/root/chatbots/bot_{username}"
            update_script_path = os.path.join(bot_project_path, "update_info.py")

            if os.path.exists(update_script_path):
                python_executable = f"/root/chatbots/bot_{username}/venv/bin/python"
                if not os.path.exists(python_executable):
                    python_executable = sys.executable

                # Executa o script usando subprocess.run para capturar a saída
                result = subprocess.run(
                    [python_executable, update_script_path, username],
                    capture_output=True,
                    text=True,
                    check=False # Impede que o programa pare se o script falhar
                )

                # Mostra a saída no console onde você roda o "runserver"
                print("--- LOGS DO SCRIPT update_info.py ---")
                print(f"Saída Padrão (Stdout):\n{result.stdout}")
                print(f"Saída de Erro (Stderr):\n{result.stderr}")
                print("-------------------------------------")

                # Verifica se o script foi executado com sucesso
                if result.returncode == 0:
                    messages.success(request, 'Informações salvas e bot atualizado com sucesso!')
                else:
                    # Se houve um erro, exibe a mensagem de erro para o usuário
                    error_log = result.stderr or "Ocorreu um erro desconhecido no script de atualização."
                    messages.error(request, f'Falha ao atualizar o bot. Erro: {error_log}')
            else:
                messages.warning(request, f'Script de gatilho (update_info.py) não encontrado para o bot_{username}.')

        except Exception as e:
            messages.error(request, f'Ocorreu um erro ao executar o gatilho: {e}')
        
        return redirect('dashboard')

    return render(request, 'add_info.html', {'info_text': bot_info.info_text if bot_info else ''})

@login_required
def auto_messages_dashboard_view(request):
    # Para a aba "Resumo": próximas mensagens agendadas
    upcoming_messages = AutomatedMessage.objects.filter(
        user=request.user,
        send_at__gte=timezone.now()
    ).order_by('send_at')

    # Para a aba "Mensagens Agendadas": lista de números únicos
    scheduled_numbers = AutomatedMessage.objects.filter(
        user=request.user
    ).values_list('phone_number', flat=True).distinct()

    context = {
        'upcoming_messages': upcoming_messages,
        'scheduled_numbers': scheduled_numbers,
    }
    return render(request, 'auto_messages_dashboard.html', context)

@login_required
def auto_messages_detail_view(request, phone_number):
    # Mostra todas as mensagens para um número específico
    messages_for_number = AutomatedMessage.objects.filter(
        user=request.user,
        phone_number=phone_number
    ).order_by('send_at')
    
    context = {
        'phone_number': phone_number,
        'messages': messages_for_number,
    }
    return render(request, 'auto_messages_detail.html', context)

@login_required
def auto_messages_form_view(request, message_id=None):
    # View única para CRIAR e EDITAR
    instance = None
    if message_id:
        instance = get_object_or_404(AutomatedMessage, id=message_id, user=request.user)

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        message = request.POST.get('message')
        send_at = request.POST.get('send_at')
        
        if instance: # Atualiza
            instance.phone_number = phone_number
            instance.message = message
            instance.send_at = send_at
            instance.save()
        else: # Cria
            AutomatedMessage.objects.create(
                user=request.user,
                phone_number=phone_number,
                message=message,
                send_at=send_at
            )
        return redirect('auto_messages_dashboard')
        
    return render(request, 'auto_messages_form.html', {'message_instance': instance})

@login_required
def auto_messages_delete_view(request, message_id):
    # Deleta uma mensagem específica
    message_to_delete = get_object_or_404(AutomatedMessage, id=message_id, user=request.user)
    if request.method == 'POST':
        phone_number = message_to_delete.phone_number
        message_to_delete.delete()
        # Redireciona para a página de detalhes do número ou para o dashboard
        return redirect('auto_messages_detail', phone_number=phone_number)
    
    # Se for GET, mostra uma página de confirmação
    return render(request, 'auto_messages_delete_confirm.html', {'message': message_to_delete})


@login_required
def consumo_view(request):
    projects = ['bot_sejasua', 'bot_model'] # Você pode buscar isso dinamicamente se preferir

    # Pega o projeto da query string ou usa o primeiro como padrão
    selected_project = request.GET.get('project', projects[0])

    # Pega o mês da query string ou usa o mais recente como padrão
    available_months = langsmith_utils.get_available_months()
    selected_month_str = request.GET.get('month', available_months[0]['value'])

    year, month = map(int, selected_month_str.split('-'))

    start_time, end_time = langsmith_utils.get_month_period(year, month)

    usage_data = {}
    daily_data = []
    error = None

    try:
        usage_data = langsmith_utils.get_token_usage_for_period(selected_project, start_time, end_time)
        daily_data = langsmith_utils.get_daily_usage_breakdown(selected_project, start_time, end_time)
        usage_data['month_name'] = calendar.month_name[month]
        usage_data['year'] = year

    except Exception as e:
        error = f"Erro ao buscar dados do LangSmith: {e}"
        logger.error(error)

    context = {
        'projects': projects,
        'selected_project': selected_project,
        'available_months': available_months,
        'selected_month': selected_month_str,
        'usage_data': usage_data,
        'daily_data': daily_data,
        'error': error,
    }
    return render(request, 'consumo.html', context)

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
import os
from .models import AutomatedMessage, BotInfo # Importe o novo modelo
from django.shortcuts import get_object_or_404

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

@login_required
def auto_messages_view(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        message = request.POST.get('message')
        send_at = request.POST.get('send_at')
        AutomatedMessage.objects.create(
            user=request.user,
            phone_number=phone_number,
            message=message,
            send_at=send_at
        )
        return redirect('dashboard')
    return render(request, 'auto_messages.html')


@login_required
def add_info_view(request):
    # Tenta buscar a informação existente para o usuário
    try:
        bot_info = BotInfo.objects.get(user=request.user)
    except BotInfo.DoesNotExist:
        bot_info = None

    if request.method == 'POST':
        info_text = request.POST.get('info_text')
        # Se a informação já existe, atualiza. Se não, cria.
        BotInfo.objects.update_or_create(
            user=request.user,
            defaults={'info_text': info_text}
        )
        return redirect('dashboard')

    # Passa a informação existente para o template
    return render(request, 'add_info.html', {'info_text': bot_info.info_text if bot_info else ''})
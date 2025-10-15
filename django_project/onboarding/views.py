from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
import os
from .models import AutomatedMessage

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
def add_info_view(request):
    if request.method == 'POST':
        info_text = request.POST.get('info_text')
        user_bot_folder = f"/root/chatbots/bot_{request.user.username}/data"
        os.makedirs(user_bot_folder, exist_ok=True)
        with open(os.path.join(user_bot_folder, "info.txt"), "w") as f:
            f.write(info_text)
        return redirect('dashboard')
    return render(request, 'add_info.html')

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
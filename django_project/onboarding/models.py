from django.db import models
from django.contrib.auth.models import User

class AutomatedMessage(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('sent', 'Enviada'),
        ('failed', 'Falhou'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contact_name = models.CharField(max_length=100, verbose_name="Nome do Contato")
    phone_number = models.CharField(max_length=20, verbose_name="Número de Telefone")
    message = models.TextField(verbose_name="Mensagem")
    send_at = models.DateTimeField(verbose_name="Data/Hora de Envio")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Enviada em")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        ordering = ['-send_at']
        verbose_name = "Mensagem Automática"
        verbose_name_plural = "Mensagens Automáticas"

    def __str__(self):
        return f"{self.contact_name} ({self.phone_number}) - {self.send_at.strftime('%d/%m/%Y %H:%M')}"

class BotInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    info_text = models.TextField(verbose_name="Informações do Bot")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Informação do Bot"
        verbose_name_plural = "Informações dos Bots"

    def __str__(self):
        return f"Informações do Bot para {self.user.username}"
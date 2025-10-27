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
    
    # Novos campos específicos
    horarios_atendimento = models.TextField(verbose_name="Horários de Atendimento", blank=True, default='')
    endereco_atendimento = models.TextField(verbose_name="Endereço de Atendimento", blank=True, default='')
    nome_profissional = models.CharField(max_length=200, verbose_name="Nome do Profissional", blank=True, default='')
    profissao = models.CharField(max_length=200, verbose_name="Profissão", blank=True, default='')
    produtos_servicos_precos = models.TextField(verbose_name="Produtos, Serviços e Preços", blank=True, default='')
    informacoes_relevantes = models.TextField(verbose_name="Informações Relevantes sobre o Negócio", blank=True, default='')
    modo_atendimento = models.TextField(verbose_name="Modo de Atendimento", blank=True, default='')
    
    # Mantém o campo antigo para compatibilidade (pode ser removido depois)
    info_text = models.TextField(verbose_name="Informações do Bot (Legado)", blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Informação do Bot"
        verbose_name_plural = "Informações dos Bots"

    def __str__(self):
        return f"Informações do Bot para {self.user.username}"


#________________________________________________________________________________________________________________________________________________


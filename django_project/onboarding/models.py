from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

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

class Plan(models.Model):
    """Planos de assinatura disponíveis"""
    
    nome = models.CharField(max_length=100, verbose_name="Nome do Plano")
    slug = models.SlugField(unique=True, verbose_name="Identificador Único")
    descricao = models.TextField(verbose_name="Descrição", blank=True)
    preco_mensal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Preço Mensal (R$)",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tokens_incluidos = models.BigIntegerField(
        verbose_name="Tokens Incluídos no Plano",
        validators=[MinValueValidator(0)],
        help_text="Quantidade de tokens inclusos no plano mensal"
    )
    ativo = models.BooleanField(default=True, verbose_name="Plano Ativo")
    ordem_exibicao = models.IntegerField(
        default=0, 
        verbose_name="Ordem de Exibição",
        help_text="Ordem em que o plano aparece na landing page (menor = primeiro)"
    )
    destaque = models.BooleanField(
        default=False, 
        verbose_name="Plano em Destaque",
        help_text="Marcar como 'Mais Popular' ou 'Recomendado'"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Plano"
        verbose_name_plural = "Planos"
        ordering = ['ordem_exibicao', 'preco_mensal']

    def __str__(self):
        return f"{self.nome} - R$ {self.preco_mensal}/mês"


class PlanFeature(models.Model):
    """Funcionalidades incluídas em cada plano"""
    
    plano = models.ForeignKey(
        Plan, 
        on_delete=models.CASCADE, 
        related_name='funcionalidades',
        verbose_name="Plano"
    )
    nome_funcionalidade = models.CharField(max_length=200, verbose_name="Nome da Funcionalidade")
    descricao = models.TextField(verbose_name="Descrição", blank=True)
    icone = models.CharField(
        max_length=50, 
        verbose_name="Ícone FontAwesome",
        blank=True,
        help_text="Ex: fa-check, fa-star, fa-rocket"
    )
    ordem = models.IntegerField(default=0, verbose_name="Ordem")
    ativo = models.BooleanField(default=True, verbose_name="Ativa")

    class Meta:
        verbose_name = "Funcionalidade do Plano"
        verbose_name_plural = "Funcionalidades dos Planos"
        ordering = ['plano', 'ordem']

    def __str__(self):
        return f"{self.plano.nome} - {self.nome_funcionalidade}"


class AdditionalFeature(models.Model):
    """Funcionalidades extras que podem ser contratadas adicionalmente"""
    
    nome = models.CharField(max_length=100, verbose_name="Nome da Funcionalidade")
    slug = models.SlugField(unique=True, verbose_name="Identificador Único")
    descricao = models.TextField(verbose_name="Descrição")
    descricao_curta = models.CharField(
        max_length=200, 
        verbose_name="Descrição Curta",
        blank=True,
        help_text="Resumo para exibição rápida"
    )
    preco_mensal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Preço Mensal Adicional (R$)",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    icone = models.CharField(
        max_length=50, 
        verbose_name="Ícone FontAwesome",
        blank=True,
        help_text="Ex: fa-calendar, fa-chart-line"
    )
    ativo = models.BooleanField(default=True, verbose_name="Disponível para Contratação")
    ordem = models.IntegerField(default=0, verbose_name="Ordem de Exibição")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Funcionalidade Extra"
        verbose_name_plural = "Funcionalidades Extras"
        ordering = ['ordem', 'nome']

    def __str__(self):
        return f"{self.nome} - R$ {self.preco_mensal}/mês"


class ClientSubscription(models.Model):
    """Assinatura de um cliente"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('active', 'Ativa'),
        ('suspended', 'Suspensa'),
        ('cancelled', 'Cancelada'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='subscription',
        verbose_name="Usuário"
    )
    plano = models.ForeignKey(
        Plan, 
        on_delete=models.PROTECT, 
        related_name='subscriptions',
        verbose_name="Plano Contratado"
    )
    funcionalidades_extras = models.ManyToManyField(
        AdditionalFeature,
        blank=True,
        related_name='subscriptions',
        verbose_name="Funcionalidades Extras Contratadas"
    )
    
    # Configurações de cobrança
    billing_day = models.IntegerField(
        verbose_name="Dia de Cobrança",
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        help_text="Dia do mês em que a cobrança é realizada (1-28)",
        default=18
    )
    
    # Controle de tokens
    tokens_incluidos_no_plano = models.BigIntegerField(
        verbose_name="Tokens Incluídos",
        help_text="Quantidade de tokens do plano (copiado do plano na contratação)"
    )
    
    # Datas e status
    data_inicio = models.DateField(verbose_name="Data de Início", default=timezone.now)
    data_cancelamento = models.DateField(
        verbose_name="Data de Cancelamento", 
        null=True, 
        blank=True
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="Status"
    )
    auto_renew = models.BooleanField(
        default=True, 
        verbose_name="Renovação Automática",
        help_text="Renovar automaticamente a cada mês"
    )
    
    # Integração com gateway de pagamento
    payment_gateway_subscription_id = models.CharField(
        max_length=200,
        verbose_name="ID da Assinatura no Gateway",
        blank=True,
        help_text="ID da assinatura recorrente no gateway de pagamento"
    )
    payment_gateway_customer_id = models.CharField(
        max_length=200,
        verbose_name="ID do Cliente no Gateway",
        blank=True,
        help_text="ID do cliente no gateway de pagamento"
    )
    
    # Observações administrativas
    notas_admin = models.TextField(
        verbose_name="Notas Administrativas",
        blank=True,
        help_text="Observações internas sobre esta assinatura"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Assinatura"
        verbose_name_plural = "Assinaturas"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.plano.nome} ({self.get_status_display()})"
    
    def get_valor_total_mensal(self):
        """Calcula o valor total mensal (plano + extras)"""
        valor = self.plano.preco_mensal
        for extra in self.funcionalidades_extras.all():
            valor += extra.preco_mensal
        return valor
    
    def get_proxima_cobranca(self):
        """Retorna a data da próxima cobrança"""
        from datetime import date
        hoje = date.today()
        
        if hoje.day < self.billing_day:
            # Próxima cobrança é neste mês
            return date(hoje.year, hoje.month, self.billing_day)
        else:
            # Próxima cobrança é no próximo mês
            if hoje.month == 12:
                return date(hoje.year + 1, 1, self.billing_day)
            else:
                return date(hoje.year, hoje.month + 1, self.billing_day)


class TokenUsage(models.Model):
    """Registro de uso de tokens por período"""
    
    subscription = models.ForeignKey(
        ClientSubscription,
        on_delete=models.CASCADE,
        related_name='token_usages',
        verbose_name="Assinatura"
    )
    
    # Período de uso
    periodo_inicio = models.DateField(verbose_name="Início do Período")
    periodo_fim = models.DateField(verbose_name="Fim do Período")
    
    # Contadores de tokens
    tokens_usados = models.BigIntegerField(
        verbose_name="Tokens Usados",
        default=0,
        validators=[MinValueValidator(0)]
    )
    tokens_incluidos = models.BigIntegerField(
        verbose_name="Tokens Incluídos no Período",
        help_text="Tokens inclusos no plano para este período"
    )
    tokens_extras = models.BigIntegerField(
        verbose_name="Tokens Extras",
        default=0,
        help_text="Tokens consumidos além do plano"
    )
    
    # Custos
    custo_extra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Custo Extra (R$)",
        default=Decimal('0.00'),
        help_text="Custo dos tokens extras consumidos"
    )
    
    # Estatísticas detalhadas
    input_tokens = models.BigIntegerField(
        verbose_name="Tokens de Entrada",
        default=0
    )
    output_tokens = models.BigIntegerField(
        verbose_name="Tokens de Saída",
        default=0
    )
    run_count = models.IntegerField(
        verbose_name="Número de Execuções",
        default=0
    )
    
    # Controle
    faturado = models.BooleanField(
        default=False,
        verbose_name="Faturado",
        help_text="Se este uso já foi incluído em uma fatura"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Uso de Tokens"
        verbose_name_plural = "Uso de Tokens"
        ordering = ['-periodo_inicio']
        unique_together = ['subscription', 'periodo_inicio']

    def __str__(self):
        return f"{self.subscription.user.username} - {self.periodo_inicio} a {self.periodo_fim}"
    
    def calcular_tokens_extras(self):
        """Calcula quantos tokens foram além do plano"""
        if self.tokens_usados > self.tokens_incluidos:
            self.tokens_extras = self.tokens_usados - self.tokens_incluidos
        else:
            self.tokens_extras = 0
        return self.tokens_extras
    
    def calcular_custo_extra(self, custo_por_token=None):
        """Calcula o custo dos tokens extras"""
        if custo_por_token is None:
            # Valor padrão baseado no custo médio (ajustar conforme necessário)
            # Exemplo: R$ 0.00006 por token (equivalente a ~$0.00001 * 6 (dólar))
            custo_por_token = Decimal('0.00006')
        
        self.custo_extra = Decimal(str(self.tokens_extras)) * custo_por_token
        return self.custo_extra


class BotInstance(models.Model):
    """Instância de bot de um cliente"""
    
    STATUS_CHOICES = [
        ('creating', 'Criando'),
        ('active', 'Ativo'),
        ('error', 'Erro'),
        ('paused', 'Pausado'),
        ('deleted', 'Deletado'),
    ]
    
    subscription = models.OneToOneField(
        ClientSubscription,
        on_delete=models.CASCADE,
        related_name='bot_instance',
        verbose_name="Assinatura"
    )
    
    # Identificação e localização
    bot_folder_name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nome da Pasta do Bot",
        help_text="Nome da pasta em /root/chatbots/"
    )
    
    # Portas
    porta_uvicorn = models.IntegerField(
        unique=True,
        verbose_name="Porta Uvicorn",
        validators=[MinValueValidator(8000), MaxValueValidator(65535)]
    )
    porta_evolution = models.IntegerField(
        unique=True,
        verbose_name="Porta Evolution API",
        validators=[MinValueValidator(8000), MaxValueValidator(65535)],
        null=True,
        blank=True
    )
    
    # Status e datas
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='creating',
        verbose_name="Status"
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    data_ativacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ativado em"
    )
    ultima_verificacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Última Verificação de Status"
    )
    
    # Integração Evolution API
    evolution_instance_id = models.CharField(
        max_length=200,
        verbose_name="ID da Instância no Evolution",
        blank=True
    )
    evolution_qrcode = models.TextField(
        verbose_name="QR Code do WhatsApp",
        blank=True,
        help_text="Base64 do QR Code para conexão"
    )
    evolution_connected = models.BooleanField(
        default=False,
        verbose_name="WhatsApp Conectado"
    )
    
    # Serviços systemd
    systemd_service_name = models.CharField(
        max_length=100,
        verbose_name="Nome do Serviço Principal",
        blank=True,
        help_text="Nome do serviço systemd do bot"
    )
    systemd_scheduler_name = models.CharField(
        max_length=100,
        verbose_name="Nome do Serviço Agendador",
        blank=True,
        help_text="Nome do serviço systemd do agendador"
    )
    
    # Logs e diagnóstico
    error_log = models.TextField(
        verbose_name="Log de Erros",
        blank=True,
        help_text="Últimos erros ocorridos"
    )
    
    # Observações
    notas_admin = models.TextField(
        verbose_name="Notas Administrativas",
        blank=True
    )
    
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Instância de Bot"
        verbose_name_plural = "Instâncias de Bots"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"{self.subscription.user.username} - {self.bot_folder_name} ({self.get_status_display()})"
    
    def get_url_bot(self):
        """Retorna a URL do bot"""
        return f"http://31.97.92.54:{self.porta_uvicorn}"
    
    def get_url_evolution(self):
        """Retorna a URL do Evolution API"""
        if self.porta_evolution:
            return f"http://31.97.92.54:{self.porta_evolution}"
        return None


class Invoice(models.Model):
    """Faturas geradas para clientes"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('paid', 'Paga'),
        ('overdue', 'Vencida'),
        ('cancelled', 'Cancelada'),
    ]
    
    subscription = models.ForeignKey(
        ClientSubscription,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name="Assinatura"
    )
    
    # Período de referência
    periodo_inicio = models.DateField(verbose_name="Início do Período")
    periodo_fim = models.DateField(verbose_name="Fim do Período")
    
    # Valores
    valor_plano = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor do Plano (R$)"
    )
    valor_funcionalidades_extras = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor Funcionalidades Extras (R$)",
        default=Decimal('0.00')
    )
    valor_tokens_extras = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor Tokens Extras (R$)",
        default=Decimal('0.00')
    )
    desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Desconto (R$)",
        default=Decimal('0.00')
    )
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor Total (R$)"
    )
    
    # Datas e status
    data_emissao = models.DateField(
        auto_now_add=True,
        verbose_name="Data de Emissão"
    )
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_pagamento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Pagamento"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    
    # Integração com gateway
    payment_id = models.CharField(
        max_length=200,
        verbose_name="ID do Pagamento no Gateway",
        blank=True
    )
    payment_url = models.URLField(
        verbose_name="URL de Pagamento",
        blank=True,
        help_text="Link para o cliente efetuar o pagamento"
    )
    
    # Detalhamento
    detalhes_json = models.JSONField(
        verbose_name="Detalhes em JSON",
        blank=True,
        null=True,
        help_text="Detalhamento completo da fatura em formato JSON"
    )
    
    # Observações
    observacoes = models.TextField(
        verbose_name="Observações",
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Fatura"
        verbose_name_plural = "Faturas"
        ordering = ['-data_emissao']

    def __str__(self):
        return f"Fatura #{self.id} - {self.subscription.user.username} - R$ {self.valor_total}"
    
    def calcular_total(self):
        """Calcula o valor total da fatura"""
        self.valor_total = (
            self.valor_plano + 
            self.valor_funcionalidades_extras + 
            self.valor_tokens_extras - 
            self.desconto
        )
        return self.valor_total
    
    def marcar_como_paga(self):
        """Marca a fatura como paga"""
        self.status = 'paid'
        self.data_pagamento = timezone.now().date()
        self.save()
    
    def verificar_vencimento(self):
        """Verifica se a fatura está vencida"""
        from datetime import date
        if self.status == 'pending' and date.today() > self.data_vencimento:
            self.status = 'overdue'
            self.save()
            return True
        return False


class PortRegistry(models.Model):
    """Registro centralizado de portas alocadas"""
    
    porta = models.IntegerField(
        unique=True,
        verbose_name="Porta",
        validators=[MinValueValidator(8000), MaxValueValidator(65535)]
    )
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('uvicorn', 'Uvicorn'),
            ('evolution', 'Evolution API'),
        ],
        verbose_name="Tipo de Serviço"
    )
    bot_instance = models.ForeignKey(
        BotInstance,
        on_delete=models.CASCADE,
        related_name='portas',
        verbose_name="Instância do Bot",
        null=True,
        blank=True
    )
    em_uso = models.BooleanField(default=True, verbose_name="Em Uso")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Alocada em")

    class Meta:
        verbose_name = "Registro de Porta"
        verbose_name_plural = "Registro de Portas"
        ordering = ['porta']

    def __str__(self):
        return f"Porta {self.porta} - {self.get_tipo_display()} {'(Em uso)' if self.em_uso else '(Livre)'}"
    
    @classmethod
    def get_proxima_porta_livre(cls, tipo='uvicorn'):
        """Retorna a próxima porta livre para o tipo especificado"""
        # Busca a maior porta usada do tipo
        ultima_porta = cls.objects.filter(tipo=tipo).order_by('-porta').first()
        
        if ultima_porta:
            proxima = ultima_porta.porta + 1
        else:
            # Primeira porta para cada tipo
            proxima = 8002 if tipo == 'uvicorn' else 8081
        
        # Verifica se já está em uso
        while cls.objects.filter(porta=proxima).exists():
            proxima += 1
        
        return proxima


# Signal para copiar tokens_incluidos do plano para a subscription
from django.db.models.signals import pre_save
from django.dispatch import receiver

@receiver(pre_save, sender=ClientSubscription)
def set_tokens_incluidos(sender, instance, **kwargs):
    """Copia tokens_incluidos do plano para a subscription se não estiver definido"""
    if not instance.tokens_incluidos_no_plano and instance.plano:
        instance.tokens_incluidos_no_plano = instance.plano.tokens_incluidos
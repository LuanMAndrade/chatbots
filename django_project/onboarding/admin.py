from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Plan, PlanFeature, AdditionalFeature, ClientSubscription,
    TokenUsage, BotInstance, Invoice, PortRegistry
)


class PlanFeatureInline(admin.TabularInline):
    """Inline para funcionalidades do plano"""
    model = PlanFeature
    extra = 1
    fields = ['nome_funcionalidade', 'descricao', 'icone', 'ordem', 'ativo']


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """Admin para Planos"""
    list_display = [
        'nome', 
        'preco_mensal_formatted', 
        'tokens_incluidos_formatted',
        'ordem_exibicao',
        'destaque_badge',
        'ativo_badge',
        'total_subscriptions'
    ]
    list_filter = ['ativo', 'destaque', 'created_at']
    search_fields = ['nome', 'slug', 'descricao']
    prepopulated_fields = {'slug': ('nome',)}
    inlines = [PlanFeatureInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'slug', 'descricao')
        }),
        ('Precificação', {
            'fields': ('preco_mensal', 'tokens_incluidos')
        }),
        ('Configurações', {
            'fields': ('ativo', 'destaque', 'ordem_exibicao')
        }),
    )
    
    def preco_mensal_formatted(self, obj):
        return f"R$ {obj.preco_mensal}"
    preco_mensal_formatted.short_description = "Preço Mensal"
    
    def tokens_incluidos_formatted(self, obj):
        return f"{obj.tokens_incluidos:,}".replace(',', '.')
    tokens_incluidos_formatted.short_description = "Tokens Incluídos"
    
    def ativo_badge(self, obj):
        if obj.ativo:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">✓ Ativo</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">✗ Inativo</span>'
        )
    ativo_badge.short_description = "Status"
    
    def destaque_badge(self, obj):
        if obj.destaque:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">⭐ Destaque</span>'
            )
        return "-"
    destaque_badge.short_description = "Destaque"
    
    def total_subscriptions(self, obj):
        total = obj.subscriptions.filter(status='active').count()
        return format_html(
            '<span style="font-weight: bold; color: #007bff;">{}</span>', total
        )
    total_subscriptions.short_description = "Assinaturas Ativas"


@admin.register(PlanFeature)
class PlanFeatureAdmin(admin.ModelAdmin):
    """Admin para Funcionalidades do Plano"""
    list_display = ['nome_funcionalidade', 'plano', 'icone', 'ordem', 'ativo']
    list_filter = ['ativo', 'plano']
    search_fields = ['nome_funcionalidade', 'descricao']
    list_editable = ['ordem', 'ativo']


@admin.register(AdditionalFeature)
class AdditionalFeatureAdmin(admin.ModelAdmin):
    """Admin para Funcionalidades Extras"""
    list_display = [
        'nome',
        'preco_mensal_formatted',
        'ordem',
        'ativo_badge',
        'total_subscriptions'
    ]
    list_filter = ['ativo', 'created_at']
    search_fields = ['nome', 'slug', 'descricao']
    prepopulated_fields = {'slug': ('nome',)}
    list_editable = ['ordem']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'slug', 'descricao', 'descricao_curta', 'icone')
        }),
        ('Precificação', {
            'fields': ('preco_mensal',)
        }),
        ('Configurações', {
            'fields': ('ativo', 'ordem')
        }),
    )
    
    def preco_mensal_formatted(self, obj):
        return f"R$ {obj.preco_mensal}"
    preco_mensal_formatted.short_description = "Preço Mensal"
    
    def ativo_badge(self, obj):
        if obj.ativo:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">✓ Disponível</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">✗ Indisponível</span>'
        )
    ativo_badge.short_description = "Status"
    
    def total_subscriptions(self, obj):
        total = obj.subscriptions.filter(status='active').count()
        return format_html(
            '<span style="font-weight: bold; color: #007bff;">{}</span>', total
        )
    total_subscriptions.short_description = "Clientes Usando"


@admin.register(ClientSubscription)
class ClientSubscriptionAdmin(admin.ModelAdmin):
    """Admin para Assinaturas"""
    list_display = [
        'user',
        'plano',
        'status_badge',
        'billing_day',
        'valor_total_formatted',
        'proxima_cobranca',
        'data_inicio',
        'bot_status'
    ]
    list_filter = ['status', 'plano', 'auto_renew', 'data_inicio']
    search_fields = ['user__username', 'user__email', 'payment_gateway_subscription_id']
    raw_id_fields = ['user']
    filter_horizontal = ['funcionalidades_extras']
    
    fieldsets = (
        ('Cliente', {
            'fields': ('user',)
        }),
        ('Plano e Extras', {
            'fields': ('plano', 'funcionalidades_extras', 'tokens_incluidos_no_plano')
        }),
        ('Cobrança', {
            'fields': ('billing_day', 'data_inicio', 'data_cancelamento', 'auto_renew')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Gateway de Pagamento', {
            'fields': ('payment_gateway_subscription_id', 'payment_gateway_customer_id'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('notas_admin',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'active': '#28a745',
            'suspended': '#dc3545',
            'cancelled': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"
    
    def valor_total_formatted(self, obj):
        valor = obj.get_valor_total_mensal()
        return f"R$ {valor}"
    valor_total_formatted.short_description = "Valor Mensal"
    
    def proxima_cobranca(self, obj):
        data = obj.get_proxima_cobranca()
        return data.strftime('%d/%m/%Y')
    proxima_cobranca.short_description = "Próxima Cobrança"
    
    def bot_status(self, obj):
        try:
            bot = obj.bot_instance
            if bot.status == 'active':
                return format_html(
                    '<span style="color: #28a745; font-weight: bold;">✓ Ativo</span>'
                )
            elif bot.status == 'creating':
                return format_html(
                    '<span style="color: #ffc107; font-weight: bold;">⏳ Criando</span>'
                )
            elif bot.status == 'error':
                return format_html(
                    '<span style="color: #dc3545; font-weight: bold;">✗ Erro</span>'
                )
            else:
                return format_html(
                    '<span style="color: #6c757d;">{}</span>', bot.get_status_display()
                )
        except BotInstance.DoesNotExist:
            return format_html(
                '<span style="color: #dc3545;">Sem bot</span>'
            )
    bot_status.short_description = "Bot"


@admin.register(TokenUsage)
class TokenUsageAdmin(admin.ModelAdmin):
    """Admin para Uso de Tokens"""
    list_display = [
        'subscription',
        'periodo',
        'tokens_usados_formatted',
        'tokens_incluidos_formatted',
        'tokens_extras_formatted',
        'custo_extra_formatted',
        'faturado_badge'
    ]
    list_filter = ['faturado', 'periodo_inicio']
    search_fields = ['subscription__user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Assinatura', {
            'fields': ('subscription',)
        }),
        ('Período', {
            'fields': ('periodo_inicio', 'periodo_fim')
        }),
        ('Tokens', {
            'fields': (
                'tokens_usados', 'tokens_incluidos', 'tokens_extras',
                'input_tokens', 'output_tokens', 'run_count'
            )
        }),
        ('Custos', {
            'fields': ('custo_extra', 'faturado')
        }),
    )
    
    def periodo(self, obj):
        return f"{obj.periodo_inicio.strftime('%d/%m/%Y')} - {obj.periodo_fim.strftime('%d/%m/%Y')}"
    periodo.short_description = "Período"
    
    def tokens_usados_formatted(self, obj):
        return f"{obj.tokens_usados:,}".replace(',', '.')
    tokens_usados_formatted.short_description = "Tokens Usados"
    
    def tokens_incluidos_formatted(self, obj):
        return f"{obj.tokens_incluidos:,}".replace(',', '.')
    tokens_incluidos_formatted.short_description = "Tokens Incluídos"
    
    def tokens_extras_formatted(self, obj):
        if obj.tokens_extras > 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">{}</span>',
                f"{obj.tokens_extras:,}".replace(',', '.')
            )
        return "0"
    tokens_extras_formatted.short_description = "Tokens Extras"
    
    def custo_extra_formatted(self, obj):
        if obj.custo_extra > 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">R$ {}</span>',
                obj.custo_extra
            )
        return "R$ 0,00"
    custo_extra_formatted.short_description = "Custo Extra"
    
    def faturado_badge(self, obj):
        if obj.faturado:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">✓ Faturado</span>'
            )
        return format_html(
            '<span style="background-color: #ffc107; color: black; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">⏳ Pendente</span>'
        )
    faturado_badge.short_description = "Status"


@admin.register(BotInstance)
class BotInstanceAdmin(admin.ModelAdmin):
    """Admin para Instâncias de Bot"""
    list_display = [
        'subscription_user',
        'bot_folder_name',
        'status_badge',
        'porta_uvicorn',
        'porta_evolution',
        'evolution_connected_badge',
        'data_criacao',
        'actions_buttons'
    ]
    list_filter = ['status', 'evolution_connected', 'data_criacao']
    search_fields = [
        'subscription__user__username',
        'bot_folder_name',
        'evolution_instance_id'
    ]
    readonly_fields = [
        'data_criacao',
        'updated_at',
        'url_bot_link',
        'url_evolution_link'
    ]
    
    fieldsets = (
        ('Assinatura', {
            'fields': ('subscription',)
        }),
        ('Identificação', {
            'fields': ('bot_folder_name',)
        }),
        ('Portas', {
            'fields': ('porta_uvicorn', 'porta_evolution')
        }),
        ('Status', {
            'fields': ('status', 'data_criacao', 'data_ativacao', 'ultima_verificacao')
        }),
        ('Evolution API', {
            'fields': (
                'evolution_instance_id',
                'evolution_connected',
                'evolution_qrcode'
            )
        }),
        ('Serviços Systemd', {
            'fields': ('systemd_service_name', 'systemd_scheduler_name')
        }),
        ('URLs', {
            'fields': ('url_bot_link', 'url_evolution_link'),
            'classes': ('collapse',)
        }),
        ('Diagnóstico', {
            'fields': ('error_log', 'notas_admin'),
            'classes': ('collapse',)
        }),
    )
    
    def subscription_user(self, obj):
        return obj.subscription.user.username
    subscription_user.short_description = "Usuário"
    
    def status_badge(self, obj):
        colors = {
            'creating': '#ffc107',
            'active': '#28a745',
            'error': '#dc3545',
            'paused': '#6c757d',
            'deleted': '#343a40',
        }
        icons = {
            'creating': '⏳',
            'active': '✓',
            'error': '✗',
            'paused': '⏸',
            'deleted': '🗑',
        }
        color = colors.get(obj.status, '#6c757d')
        icon = icons.get(obj.status, '●')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_badge.short_description = "Status"
    
    def evolution_connected_badge(self, obj):
        if obj.evolution_connected:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Conectado</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">✗ Desconectado</span>'
        )
    evolution_connected_badge.short_description = "WhatsApp"
    
    def url_bot_link(self, obj):
        url = obj.get_url_bot()
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    url_bot_link.short_description = "URL do Bot"
    
    def url_evolution_link(self, obj):
        url = obj.get_url_evolution()
        if url:
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return "-"
    url_evolution_link.short_description = "URL Evolution API"
    
    def actions_buttons(self, obj):
        if obj.status == 'active':
            return format_html(
                '<a class="button" href="#" style="padding: 5px 10px; background: #17a2b8; '
                'color: white; border-radius: 3px; text-decoration: none;">🔄 Reiniciar</a> '
                '<a class="button" href="#" style="padding: 5px 10px; background: #ffc107; '
                'color: black; border-radius: 3px; text-decoration: none;">⏸ Pausar</a>'
            )
        return "-"
    actions_buttons.short_description = "Ações"


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin para Faturas"""
    list_display = [
        'invoice_number',
        'subscription_user',
        'periodo',
        'valor_total_formatted',
        'status_badge',
        'data_vencimento',
        'data_pagamento'
    ]
    list_filter = ['status', 'data_emissao', 'data_vencimento']
    search_fields = [
        'subscription__user__username',
        'payment_id'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'valor_total_calculado',
        'payment_url_link'
    ]
    
    fieldsets = (
        ('Assinatura', {
            'fields': ('subscription',)
        }),
        ('Período', {
            'fields': ('periodo_inicio', 'periodo_fim')
        }),
        ('Valores', {
            'fields': (
                'valor_plano',
                'valor_funcionalidades_extras',
                'valor_tokens_extras',
                'desconto',
                'valor_total',
                'valor_total_calculado'
            )
        }),
        ('Datas', {
            'fields': (
                'data_emissao',
                'data_vencimento',
                'data_pagamento'
            )
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Pagamento', {
            'fields': (
                'payment_id',
                'payment_url',
                'payment_url_link'
            ),
            'classes': ('collapse',)
        }),
        ('Detalhes', {
            'fields': ('detalhes_json', 'observacoes'),
            'classes': ('collapse',)
        }),
    )
    
    def invoice_number(self, obj):
        return f"#{obj.id:06d}"
    invoice_number.short_description = "Nº Fatura"
    
    def subscription_user(self, obj):
        return obj.subscription.user.username
    subscription_user.short_description = "Cliente"
    
    def periodo(self, obj):
        return f"{obj.periodo_inicio.strftime('%d/%m/%Y')} - {obj.periodo_fim.strftime('%d/%m/%Y')}"
    periodo.short_description = "Período"
    
    def valor_total_formatted(self, obj):
        return format_html(
            '<span style="font-weight: bold; font-size: 14px;">R$ {}</span>',
            obj.valor_total
        )
    valor_total_formatted.short_description = "Valor Total"
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'paid': '#28a745',
            'overdue': '#dc3545',
            'cancelled': '#6c757d',
        }
        icons = {
            'pending': '⏳',
            'paid': '✓',
            'overdue': '⚠',
            'cancelled': '✗',
        }
        color = colors.get(obj.status, '#6c757d')
        icon = icons.get(obj.status, '●')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_badge.short_description = "Status"
    
    def valor_total_calculado(self, obj):
        return f"R$ {obj.calcular_total()}"
    valor_total_calculado.short_description = "Total Calculado"
    
    def payment_url_link(self, obj):
        if obj.payment_url:
            return format_html(
                '<a href="{}" target="_blank">Abrir link de pagamento</a>',
                obj.payment_url
            )
        return "-"
    payment_url_link.short_description = "Link de Pagamento"


@admin.register(PortRegistry)
class PortRegistryAdmin(admin.ModelAdmin):
    """Admin para Registro de Portas"""
    list_display = [
        'porta',
        'tipo',
        'bot_user',
        'em_uso_badge',
        'created_at'
    ]
    list_filter = ['tipo', 'em_uso', 'created_at']
    search_fields = ['porta', 'bot_instance__subscription__user__username']
    
    def bot_user(self, obj):
        if obj.bot_instance:
            return obj.bot_instance.subscription.user.username
        return "-"
    bot_user.short_description = "Usuário"
    
    def em_uso_badge(self, obj):
        if obj.em_uso:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">✓ Em Uso</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">○ Livre</span>'
        )
    em_uso_badge.short_description = "Status"
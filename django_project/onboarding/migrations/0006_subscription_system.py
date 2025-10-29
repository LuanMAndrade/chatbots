# Generated migration for new subscription system models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('onboarding', '0005_add_botinfo_fields'),
    ]

    operations = [
        # Plan
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome do Plano')),
                ('slug', models.SlugField(unique=True, verbose_name='Identificador Único')),
                ('descricao', models.TextField(blank=True, verbose_name='Descrição')),
                ('preco_mensal', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Preço Mensal (R$)')),
                ('tokens_incluidos', models.BigIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Tokens Incluídos no Plano')),
                ('ativo', models.BooleanField(default=True, verbose_name='Plano Ativo')),
                ('ordem_exibicao', models.IntegerField(default=0, verbose_name='Ordem de Exibição')),
                ('destaque', models.BooleanField(default=False, verbose_name='Plano em Destaque')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
            ],
            options={
                'verbose_name': 'Plano',
                'verbose_name_plural': 'Planos',
                'ordering': ['ordem_exibicao', 'preco_mensal'],
            },
        ),
        
        # PlanFeature
        migrations.CreateModel(
            name='PlanFeature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_funcionalidade', models.CharField(max_length=200, verbose_name='Nome da Funcionalidade')),
                ('descricao', models.TextField(blank=True, verbose_name='Descrição')),
                ('icone', models.CharField(blank=True, max_length=50, verbose_name='Ícone FontAwesome')),
                ('ordem', models.IntegerField(default=0, verbose_name='Ordem')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativa')),
                ('plano', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='funcionalidades', to='onboarding.plan', verbose_name='Plano')),
            ],
            options={
                'verbose_name': 'Funcionalidade do Plano',
                'verbose_name_plural': 'Funcionalidades dos Planos',
                'ordering': ['plano', 'ordem'],
            },
        ),
        
        # AdditionalFeature
        migrations.CreateModel(
            name='AdditionalFeature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome da Funcionalidade')),
                ('slug', models.SlugField(unique=True, verbose_name='Identificador Único')),
                ('descricao', models.TextField(verbose_name='Descrição')),
                ('descricao_curta', models.CharField(blank=True, max_length=200, verbose_name='Descrição Curta')),
                ('preco_mensal', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Preço Mensal Adicional (R$)')),
                ('icone', models.CharField(blank=True, max_length=50, verbose_name='Ícone FontAwesome')),
                ('ativo', models.BooleanField(default=True, verbose_name='Disponível para Contratação')),
                ('ordem', models.IntegerField(default=0, verbose_name='Ordem de Exibição')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
            ],
            options={
                'verbose_name': 'Funcionalidade Extra',
                'verbose_name_plural': 'Funcionalidades Extras',
                'ordering': ['ordem', 'nome'],
            },
        ),
        
        # ClientSubscription
        migrations.CreateModel(
            name='ClientSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('billing_day', models.IntegerField(default=18, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(28)], verbose_name='Dia de Cobrança')),
                ('tokens_incluidos_no_plano', models.BigIntegerField(verbose_name='Tokens Incluídos')),
                ('data_inicio', models.DateField(verbose_name='Data de Início')),
                ('data_cancelamento', models.DateField(blank=True, null=True, verbose_name='Data de Cancelamento')),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('active', 'Ativa'), ('suspended', 'Suspensa'), ('cancelled', 'Cancelada')], default='pending', max_length=20, verbose_name='Status')),
                ('auto_renew', models.BooleanField(default=True, verbose_name='Renovação Automática')),
                ('payment_gateway_subscription_id', models.CharField(blank=True, max_length=200, verbose_name='ID da Assinatura no Gateway')),
                ('payment_gateway_customer_id', models.CharField(blank=True, max_length=200, verbose_name='ID do Cliente no Gateway')),
                ('notas_admin', models.TextField(blank=True, verbose_name='Notas Administrativas')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('funcionalidades_extras', models.ManyToManyField(blank=True, related_name='subscriptions', to='onboarding.additionalfeature', verbose_name='Funcionalidades Extras Contratadas')),
                ('plano', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subscriptions', to='onboarding.plan', verbose_name='Plano Contratado')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Assinatura',
                'verbose_name_plural': 'Assinaturas',
                'ordering': ['-created_at'],
            },
        ),
        
        # TokenUsage
        migrations.CreateModel(
            name='TokenUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('periodo_inicio', models.DateField(verbose_name='Início do Período')),
                ('periodo_fim', models.DateField(verbose_name='Fim do Período')),
                ('tokens_usados', models.BigIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Tokens Usados')),
                ('tokens_incluidos', models.BigIntegerField(verbose_name='Tokens Incluídos no Período')),
                ('tokens_extras', models.BigIntegerField(default=0, verbose_name='Tokens Extras')),
                ('custo_extra', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='Custo Extra (R$)')),
                ('input_tokens', models.BigIntegerField(default=0, verbose_name='Tokens de Entrada')),
                ('output_tokens', models.BigIntegerField(default=0, verbose_name='Tokens de Saída')),
                ('run_count', models.IntegerField(default=0, verbose_name='Número de Execuções')),
                ('faturado', models.BooleanField(default=False, verbose_name='Faturado')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='token_usages', to='onboarding.clientsubscription', verbose_name='Assinatura')),
            ],
            options={
                'verbose_name': 'Uso de Tokens',
                'verbose_name_plural': 'Uso de Tokens',
                'ordering': ['-periodo_inicio'],
                'unique_together': {('subscription', 'periodo_inicio')},
            },
        ),
        
        # BotInstance
        migrations.CreateModel(
            name='BotInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bot_folder_name', models.CharField(max_length=100, unique=True, verbose_name='Nome da Pasta do Bot')),
                ('porta_uvicorn', models.IntegerField(unique=True, validators=[django.core.validators.MinValueValidator(8000), django.core.validators.MaxValueValidator(65535)], verbose_name='Porta Uvicorn')),
                ('porta_evolution', models.IntegerField(blank=True, null=True, unique=True, validators=[django.core.validators.MinValueValidator(8000), django.core.validators.MaxValueValidator(65535)], verbose_name='Porta Evolution API')),
                ('status', models.CharField(choices=[('creating', 'Criando'), ('active', 'Ativo'), ('error', 'Erro'), ('paused', 'Pausado'), ('deleted', 'Deletado')], default='creating', max_length=20, verbose_name='Status')),
                ('data_criacao', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('data_ativacao', models.DateTimeField(blank=True, null=True, verbose_name='Ativado em')),
                ('ultima_verificacao', models.DateTimeField(blank=True, null=True, verbose_name='Última Verificação de Status')),
                ('evolution_instance_id', models.CharField(blank=True, max_length=200, verbose_name='ID da Instância no Evolution')),
                ('evolution_qrcode', models.TextField(blank=True, verbose_name='QR Code do WhatsApp')),
                ('evolution_connected', models.BooleanField(default=False, verbose_name='WhatsApp Conectado')),
                ('systemd_service_name', models.CharField(blank=True, max_length=100, verbose_name='Nome do Serviço Principal')),
                ('systemd_scheduler_name', models.CharField(blank=True, max_length=100, verbose_name='Nome do Serviço Agendador')),
                ('error_log', models.TextField(blank=True, verbose_name='Log de Erros')),
                ('notas_admin', models.TextField(blank=True, verbose_name='Notas Administrativas')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('subscription', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bot_instance', to='onboarding.clientsubscription', verbose_name='Assinatura')),
            ],
            options={
                'verbose_name': 'Instância de Bot',
                'verbose_name_plural': 'Instâncias de Bots',
                'ordering': ['-data_criacao'],
            },
        ),
        
        # Invoice
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('periodo_inicio', models.DateField(verbose_name='Início do Período')),
                ('periodo_fim', models.DateField(verbose_name='Fim do Período')),
                ('valor_plano', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Valor do Plano (R$)')),
                ('valor_funcionalidades_extras', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='Valor Funcionalidades Extras (R$)')),
                ('valor_tokens_extras', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='Valor Tokens Extras (R$)')),
                ('desconto', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='Desconto (R$)')),
                ('valor_total', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Valor Total (R$)')),
                ('data_emissao', models.DateField(auto_now_add=True, verbose_name='Data de Emissão')),
                ('data_vencimento', models.DateField(verbose_name='Data de Vencimento')),
                ('data_pagamento', models.DateField(blank=True, null=True, verbose_name='Data de Pagamento')),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('paid', 'Paga'), ('overdue', 'Vencida'), ('cancelled', 'Cancelada')], default='pending', max_length=20, verbose_name='Status')),
                ('payment_id', models.CharField(blank=True, max_length=200, verbose_name='ID do Pagamento no Gateway')),
                ('payment_url', models.URLField(blank=True, verbose_name='URL de Pagamento')),
                ('detalhes_json', models.JSONField(blank=True, null=True, verbose_name='Detalhes em JSON')),
                ('observacoes', models.TextField(blank=True, verbose_name='Observações')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='onboarding.clientsubscription', verbose_name='Assinatura')),
            ],
            options={
                'verbose_name': 'Fatura',
                'verbose_name_plural': 'Faturas',
                'ordering': ['-data_emissao'],
            },
        ),
        
        # PortRegistry
        migrations.CreateModel(
            name='PortRegistry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('porta', models.IntegerField(unique=True, validators=[django.core.validators.MinValueValidator(8000), django.core.validators.MaxValueValidator(65535)], verbose_name='Porta')),
                ('tipo', models.CharField(choices=[('uvicorn', 'Uvicorn'), ('evolution', 'Evolution API')], max_length=20, verbose_name='Tipo de Serviço')),
                ('em_uso', models.BooleanField(default=True, verbose_name='Em Uso')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Alocada em')),
                ('bot_instance', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='portas', to='onboarding.botinstance', verbose_name='Instância do Bot')),
            ],
            options={
                'verbose_name': 'Registro de Porta',
                'verbose_name_plural': 'Registro de Portas',
                'ordering': ['porta'],
            },
        ),
    ]
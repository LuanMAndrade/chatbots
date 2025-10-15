# Generated migration file

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0002_botinfo'),
    ]

    operations = [
        # Adiciona o campo contact_name (permitindo null temporariamente)
        migrations.AddField(
            model_name='automatedmessage',
            name='contact_name',
            field=models.CharField(max_length=100, null=True, verbose_name='Nome do Contato'),
        ),
        
        # Adiciona o campo status
        migrations.AddField(
            model_name='automatedmessage',
            name='status',
            field=models.CharField(
                choices=[('pending', 'Pendente'), ('sent', 'Enviada'), ('failed', 'Falhou')],
                default='pending',
                max_length=10,
                verbose_name='Status'
            ),
        ),
        
        # Adiciona o campo sent_at
        migrations.AddField(
            model_name='automatedmessage',
            name='sent_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Enviada em'),
        ),
        
        # Adiciona o campo created_at
        migrations.AddField(
            model_name='automatedmessage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Criada em'),
            preserve_default=False,
        ),
        
        # Adiciona o campo updated_at
        migrations.AddField(
            model_name='automatedmessage',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Atualizada em'),
        ),
        
        # Adiciona campos de timestamp ao BotInfo também
        migrations.AddField(
            model_name='botinfo',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Criada em'),
            preserve_default=False,
        ),
        
        migrations.AddField(
            model_name='botinfo',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Atualizada em'),
        ),
        
        # Altera a ordering do modelo
        migrations.AlterModelOptions(
            name='automatedmessage',
            options={'ordering': ['-send_at'], 'verbose_name': 'Mensagem Automática', 'verbose_name_plural': 'Mensagens Automáticas'},
        ),
        
        migrations.AlterModelOptions(
            name='botinfo',
            options={'verbose_name': 'Informação do Bot', 'verbose_name_plural': 'Informações dos Bots'},
        ),
    ]
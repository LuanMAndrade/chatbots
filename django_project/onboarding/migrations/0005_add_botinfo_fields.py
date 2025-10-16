# django_project/onboarding/migrations/0005_add_botinfo_fields.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0004_alter_automatedmessage_contact_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='botinfo',
            name='horarios_atendimento',
            field=models.TextField(blank=True, default='', verbose_name='Horários de Atendimento'),
        ),
        migrations.AddField(
            model_name='botinfo',
            name='endereco_atendimento',
            field=models.TextField(blank=True, default='', verbose_name='Endereço de Atendimento'),
        ),
        migrations.AddField(
            model_name='botinfo',
            name='nome_profissional',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Nome do Profissional'),
        ),
        migrations.AddField(
            model_name='botinfo',
            name='profissao',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Profissão'),
        ),
        migrations.AddField(
            model_name='botinfo',
            name='produtos_servicos_precos',
            field=models.TextField(blank=True, default='', verbose_name='Produtos, Serviços e Preços'),
        ),
        migrations.AddField(
            model_name='botinfo',
            name='informacoes_relevantes',
            field=models.TextField(blank=True, default='', verbose_name='Informações Relevantes sobre o Negócio'),
        ),
        migrations.AddField(
            model_name='botinfo',
            name='modo_atendimento',
            field=models.TextField(blank=True, default='', verbose_name='Modo de Atendimento'),
        ),
        migrations.AlterField(
            model_name='botinfo',
            name='info_text',
            field=models.TextField(blank=True, default='', verbose_name='Informações do Bot (Legado)'),
        ),
    ]
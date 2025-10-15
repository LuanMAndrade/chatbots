# django_project/onboarding/management/commands/populate_contact_names.py
# Execute com: python manage.py populate_contact_names

from django.core.management.base import BaseCommand
from onboarding.models import AutomatedMessage


class Command(BaseCommand):
    help = 'Popula o campo contact_name para mensagens existentes'

    def handle(self, *args, **kwargs):
        messages_without_name = AutomatedMessage.objects.filter(contact_name__isnull=True)
        count = messages_without_name.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('Todas as mensagens já possuem nome de contato'))
            return
        
        self.stdout.write(f'Encontradas {count} mensagens sem nome de contato')
        
        for msg in messages_without_name:
            # Define o nome como o número de telefone se não existir
            msg.contact_name = msg.phone_number
            msg.save()
            self.stdout.write(f'  - Atualizada mensagem ID {msg.id}')
        
        self.stdout.write(self.style.SUCCESS(f'✓ {count} mensagens atualizadas com sucesso!'))
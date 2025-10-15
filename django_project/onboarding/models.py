from django.db import models
from django.contrib.auth.models import User

class AutomatedMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    message = models.TextField()
    send_at = models.DateTimeField()

    def __str__(self):
        return f"Mensagem para {self.phone_number} agendada para {self.send_at}"
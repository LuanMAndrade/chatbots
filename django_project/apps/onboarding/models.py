from django.db import models
from django.contrib.auth.models import User

class BusinessProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    owner_name = models.CharField(max_length=200)
    profession = models.CharField(max_length=200)
    service_description = models.TextField()
    business_rules = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

def document_upload_path(instance, filename):
    # Gera um caminho único para o documento dentro da pasta do chatbot
    instance_name = f"bot_{instance.business_profile.user.username}"
    return f"/root/chatbots/{instance_name}/data/documents/{filename}"

class BusinessDocument(models.Model):
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='documents')
    document_file = models.FileField(upload_to=document_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
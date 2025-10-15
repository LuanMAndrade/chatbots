from django.contrib import admin
from django.urls import path, include
from onboarding import views as onboarding_views # IMPORTANTE: Adicione esta linha

urlpatterns = [
    # ADICIONADO: Redireciona a página inicial para a view de login
    path('', onboarding_views.login_view, name='home'), 
    
    path('admin/', admin.site.urls),
    path('', include('onboarding.urls')),
]
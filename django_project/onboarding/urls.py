from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('add_info/', views.add_info_view, name='add_info'),

    # Novas URLs para Mensagens Automáticas
    path('auto_messages/', views.auto_messages_dashboard_view, name='auto_messages_dashboard'),
    path('auto_messages/new/', views.auto_messages_form_view, name='auto_messages_new'),
    path('auto_messages/phone/<str:phone_number>/', views.auto_messages_detail_view, name='auto_messages_detail'),
    path('auto_messages/edit/<int:message_id>/', views.auto_messages_form_view, name='auto_messages_edit'),
    path('auto_messages/delete/<int:message_id>/', views.auto_messages_delete_view, name='auto_messages_delete'),
    path('consumo/', views.consumo_view, name='consumo'),
    path('profile/', views.profile_view, name='profile'),
    path('clear-contacts/', views.clear_whatsapp_contacts_view, name='clear_contacts'),

    # Novas URLs - Fase 2
    path('planos/', views.landing_page, name='landing_page'),
    path('checkout/<int:plan_id>/', views.checkout_view, name='checkout'),
    path('success/', views.success_view, name='success'),
    path('payment-pending/', views.payment_pending_view, name='payment_pending'),
    path('my-subscription/', views.my_subscription_view, name='my_subscription'),
    path('cancel-subscription/', views.cancel_subscription_view, name='cancel_subscription'),
    path('check-username/', views.check_username_availability, name='check_username'),
    path('check-email/', views.check_email_availability, name='check_email'),
    path('check-cpf/', views.check_cpf_availability, name='check_cpf'),
    path('check-name/', views.check_name_availability, name='check_name'),
    
    # Webhook Asaas
    path('webhooks/asaas/', views.asaas_webhook, name='asaas_webhook'),
]
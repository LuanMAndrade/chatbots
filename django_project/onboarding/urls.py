from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('add_info/', views.add_info_view, name='add_info'),

    # Novas URLs para Mensagens Automáticas
    path('auto_messages/', views.auto_messages_dashboard_view, name='auto_messages_dashboard'),
    path('auto_messages/new/', views.auto_messages_form_view, name='auto_messages_new'),
    path('auto_messages/phone/<str:phone_number>/', views.auto_messages_detail_view, name='auto_messages_detail'),
    path('auto_messages/edit/<int:message_id>/', views.auto_messages_form_view, name='auto_messages_edit'),
    path('auto_messages/delete/<int:message_id>/', views.auto_messages_delete_view, name='auto_messages_delete'),
    path('consumo/', views.consumo_view, name='consumo'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('add_info/', views.add_info_view, name='add_info'),
    path('auto_messages/', views.auto_messages_view, name='auto_messages'),
]
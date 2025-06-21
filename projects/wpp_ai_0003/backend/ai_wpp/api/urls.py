
# api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('hello/', views.hello_world, name='hello_world'),
    path('profile/', views.user_profile, name='user_profile'),
    path('login/', views.login, name='login'),
    path('message/', views.handle_whatsapp_message, name='message'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('process/', views.process_message, name='process_message'),
    path('history/<str:phone_number>/', views.get_conversation_history, name='conversation_history'),
    path('health/', views.health_check, name='health_check'),
]
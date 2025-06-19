# api/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hello_world(request):
    """
    Endpoint protegido que retorna Hello World
    Requer:
    1. Autenticação JWT válida
    2. POST com mensagem "Olá" no corpo da requisição
    
    Exemplo de uso:
    POST /api/hello/
    Authorization: Bearer <seu_token>
    Content-Type: application/json
    
    {
        "message": "Olá"
    }
    """
    # Verificar se existe mensagem no corpo da requisição
    if not request.data:
        return Response({
            'error': 'Corpo da requisição vazio',
            'required': 'Envie {"message": "Olá"} no corpo da requisição'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verificar se a chave 'message' existe
    message = request.data.get('message')
    if not message:
        return Response({
            'error': 'Campo "message" não encontrado',
            'required': 'Envie {"message": "Olá"} no corpo da requisição'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verificar se a mensagem é exatamente "Olá"
    if message != "Olá":
        return Response({
            'error': f'Mensagem incorreta. Recebido: "{message}"',
            'required': 'A mensagem deve ser exatamente "Olá"'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Se chegou até aqui, está tudo correto!
    return Response({
        'success': True,
        'message': 'Hello World!',
        'received_message': message,
        'user': request.user.username,
        'user_id': request.user.id,
        'authenticated': True,
        'timestamp': request.META.get('HTTP_DATE')
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Endpoint que retorna informações do usuário autenticado
    """
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'date_joined': user.date_joined
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def login(request):
    """
    Endpoint de login que retorna tokens JWT
    
    Exemplo de uso:
    POST /api/login/
    Content-Type: application/json
    
    {
        "username": "seu_usuario",
        "password": "sua_senha"
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'Username e password são obrigatórios'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Autenticar usuário
    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response({
            'error': 'Credenciais inválidas'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.is_active:
        return Response({
            'error': 'Usuário inativo'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Gerar tokens JWT
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        },
        'token_type': 'Bearer'
    }, status=status.HTTP_200_OK)
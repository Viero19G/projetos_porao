# api/views.py

import os
import tempfile
import mimetypes
from io import BytesIO
from gtts import gTTS # Importação para gTTS
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

# Importação para o cache do Django
from django.core.cache import cache
import time # Para obter o timestamp atual

# --- Importações para Transcrição Offline (Vosk) ---
from vosk import Model, KaldiRecognizer, SetLogLevel
import json
import wave
import base64
from pydub import AudioSegment
# --- Fim das Importações para Transcrição Offline ---

# --- Importar o serviço OpenAI ---
from .services import openai_service
# --- Fim da Importação ---


# --- Configuração do Vosk (Transcrição Offline) ---
VOSK_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vosk_model', 'vosk-model-small-pt-0.3')

if not os.path.exists(VOSK_MODEL_PATH):
    raise Exception(f"Modelo Vosk não encontrado em: {VOSK_MODEL_PATH}. Por favor, baixe e extraia o modelo.")

SetLogLevel(-1)
vosk_model = Model(VOSK_MODEL_PATH)
# --- Fim da Configuração do Vosk ---

# --- Configuração do Piper TTS (REMOVIDO / COMENTADO, pois estamos usando gTTS) ---
# As linhas relacionadas à configuração e importação do Piper foram removidas
# para evitar confusão e garantir que apenas o gTTS seja usado para síntese de voz.
# --- Fim da Configuração do Piper TTS ---


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hello_world(request):
    """
    Endpoint protegido que retorna Hello World
    Requer:
    1. Autenticação JWT válida
    2. POST com mensagem "Olá" no corpo da requisição
    """
    if not request.data:
        return Response({
            'error': 'Corpo da requisição vazio',
            'required': 'Envie {"message": "Olá"} no corpo da requisição'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    message = request.data.get('message')
    if not message:
        return Response({
            'error': 'Campo "message" não encontrado',
            'required': 'Envie {"message": "Olá"} no corpo da requisição'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if message != "Olá":
        return Response({
            'error': f'Mensagem incorreta. Recebido: "{message}"',
            'required': 'A mensagem deve ser exatamente "Olá"'
        }, status=status.HTTP_403_FORBIDDEN)
    
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
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'Username e password são obrigatórios'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response({
            'error': 'Credenciais inválidas'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.is_active:
        return Response({
            'error': 'Usuário inativo'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_whatsapp_message(request):
    """
    Endpoint para lidar com mensagens recebidas do WhatsApp.
    Processa áudio (transcreve com Vosk, responde com OpenAI, gera áudio com gTTS ou texto)
    e texto (responde com OpenAI). Outros tipos de mídia são apenas confirmados.

    Retorna JSON para todos os tipos de resposta (incluindo áudio como Base64).
    Implementa um limite de 3 áudios por user_id a cada 24 horas.
    """
    message_type = request.data.get('type')

    if not message_type:
        return Response(
            {'status': 'error', 'message': 'Tipo de mensagem não especificado.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    whatsapp_user_id = request.data.get('user_id')
    
    # Chave do cache para o contador de áudios e o timestamp do último reset
    AUDIO_COUNT_KEY = f'audio_count_{whatsapp_user_id}'
    LAST_RESET_TIME_KEY = f'last_reset_time_{whatsapp_user_id}'
    
    # Tempo de expiração para 24 horas em segundos (24 * 60 * 60)
    EXPIRE_TIME = 24 * 3600 

    # --- Variáveis para armazenar caminhos de arquivos temporários para limpeza no finally ---
    temp_input_audio_path = None
    temp_wav_path = None
    temp_response_ogg_path = None # Usado para gTTS

    try:
        # --- Lógica para lidar com mensagens de ÁUDIO ---
        if message_type == 'audio':
            audio_file = request.FILES.get('audio_file')

            if not audio_file:
                return Response(
                    {'status': 'error', 'message': 'Nenhum arquivo de áudio fornecido.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            original_filename = audio_file.name
            original_ext = os.path.splitext(original_filename)[1]

            # 1. Salvar o arquivo de áudio de entrada temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix=original_ext) as temp_input_audio_file:
                for chunk in audio_file.chunks():
                    temp_input_audio_file.write(chunk)
                temp_input_audio_path = temp_input_audio_file.name

            # 2. Converter para WAV (PCM, mono, 16kHz) para Vosk
            try:
                audio_segment = AudioSegment.from_file(temp_input_audio_path)
                audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)

                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav_file:
                    audio_segment.export(temp_wav_file.name, format="wav")
                    temp_wav_path = temp_wav_file.name
                print(f"Áudio recebido convertido para WAV (16kHz, mono): {temp_wav_path}")

            except Exception as e:
                print(f"Erro ao converter áudio com pydub para Vosk: {e}")
                return Response(
                    {'status': 'error', 'message': f'Erro ao preparar áudio para transcrição: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # 3. Transcrever áudio usando Vosk (offline)
            transcribed_text = ""
            try:
                rec = KaldiRecognizer(vosk_model, 16000)
                with wave.open(temp_wav_path, "rb") as wf:
                    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                        raise Exception("Arquivo WAV deve ser mono, 16-bit PCM e 16kHz")

                    while True:
                        data = wf.readframes(4000)
                        if len(data) == 0:
                            break
                        if rec.AcceptWaveform(data):
                            result = json.loads(rec.Result())
                            transcribed_text += result.get('text', '') + " "

                    result = json.loads(rec.FinalResult())
                    transcribed_text += result.get('text', '')

                transcribed_text = transcribed_text.strip()
                print(f"Áudio transcrito (Vosk): {transcribed_text}")

            except Exception as e:
                print(f"Erro na transcrição com Vosk: {e}")
                transcribed_text = "" # Garante que transcribed_text seja vazio em caso de erro

            if not transcribed_text:
                return Response(
                    {'status': 'error', 'message': 'Não foi possível transcrever o áudio com Vosk ou áudio sem fala detectada.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 4. Gerar resposta com modelo de linguagem OpenAI (via serviço)
            model_response_text = openai_service.get_chat_response(whatsapp_user_id, transcribed_text)
            print(f"Resposta do modelo: {model_response_text}")

            # --- Lógica de controle de limite de áudio ---
            current_audio_count = cache.get(AUDIO_COUNT_KEY, 0)
            last_reset_time = cache.get(LAST_RESET_TIME_KEY, 0)
            
            current_time = time.time()

            # Reseta o contador se 24 horas se passaram desde o último reset
            if (current_time - last_reset_time) >= EXPIRE_TIME:
                current_audio_count = 0
                # O tempo de vida do last_reset_time é estendido para garantir que ele sobreviva 24h
                # caso o cache limpe antes do próximo reset natural.
                cache.set(LAST_RESET_TIME_KEY, current_time, EXPIRE_TIME * 2) 
                print(f"Contador de áudios para {whatsapp_user_id} resetado. Novo count: {current_audio_count}")

            if current_audio_count < 3:
                # 5. Converter texto em áudio com gTTS (online)
                try:
                    tts = gTTS(text=model_response_text, lang='pt', slow=False)
                    
                    audio_bytes_io = BytesIO()
                    tts.write_to_fp(audio_bytes_io)
                    audio_bytes_io.seek(0) # Volta para o início do buffer

                    audio_segment_response = AudioSegment.from_file(audio_bytes_io, format="mp3")
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_response_ogg_file:
                        audio_segment_response.export(temp_response_ogg_file.name, format="ogg", codec="libopus")
                        temp_response_ogg_path = temp_response_ogg_file.name
                    
                    if not os.path.exists(temp_response_ogg_path) or os.path.getsize(temp_response_ogg_path) == 0:
                        raise Exception(f"Erro: Arquivo OGG exportado ({temp_response_ogg_path}) está vazio ou não existe.")

                    print(f"Resposta de áudio gerada (gTTS) e salva como OGG: {temp_response_ogg_path}")

                    # 6. Ler o arquivo OGG final em Base64 e retornar no JSON
                    with open(temp_response_ogg_path, 'rb') as audio_file_to_send:
                        audio_response_base64 = base64.b64encode(audio_file_to_send.read()).decode('utf-8')
                    
                    print(f"DEBUG: Áudio Base64 de resposta pronto para envio. Tamanho: {len(audio_response_base64)} bytes.")

                    # Incrementa o contador de áudios e define o tempo de vida do cache
                    cache.set(AUDIO_COUNT_KEY, current_audio_count + 1, EXPIRE_TIME * 2) 
                    print(f"Áudio {current_audio_count + 1}/3 para {whatsapp_user_id}. Respondendo com áudio.")

                    return Response(
                        {
                            'status': 'success',
                            'type': 'audio',
                            'response': audio_response_base64,
                            'mime_type': 'audio/ogg'
                        },
                        status=status.HTTP_200_OK
                    )

                except Exception as e:
                    print(f"Erro na geração de fala com gTTS ou processamento final: {e}")
                    # Se houver erro no gTTS, ainda assim retorna texto para não interromper
                    return Response(
                        {'status': 'success', 'type': 'text', 'response': model_response_text},
                        status=status.HTTP_200_OK
                    )
            else:
                # Limite de áudios atingido, retorna resposta em texto
                print(f"Limite de áudios (3) atingido para {whatsapp_user_id}. Respondendo com texto.")
                return Response(
                    {'status': 'success', 'type': 'text', 'response': model_response_text},
                    status=status.HTTP_200_OK
                )


        # --- Lógica para lidar com mensagens de TEXTO (sem alterações significativas) ---
        elif message_type == 'text':
            received_text = request.data.get('content')
            if not received_text:
                return Response(
                    {'status': 'error', 'message': 'Nenhum texto fornecido.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            model_response_text = openai_service.get_chat_response(whatsapp_user_id, received_text)
            return Response(
                {'status': 'success', 'type': 'text', 'response': model_response_text},
                status=status.HTTP_200_OK
            )

        # --- Lógica para o comando de limpar histórico ---
        elif message_type == 'command' and request.data.get('command') == 'clear_history':
            if openai_service.clear_history(whatsapp_user_id):
                # Opcional: também resetar o contador de áudios quando o histórico é limpo
                cache.set(AUDIO_COUNT_KEY, 0, EXPIRE_TIME * 2)
                cache.set(LAST_RESET_TIME_KEY, time.time(), EXPIRE_TIME * 2)
                
                return Response(
                    {'status': 'success', 'type': 'command_response', 'response': 'Histórico de conversa limpo!'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'status': 'success', 'type': 'command_response', 'response': 'Nenhum histórico para limpar.'},
                    status=status.HTTP_200_OK
                )

        # --- Lógica para lidar com outros tipos de mensagem (imagem, vídeo, documento) ---
        elif message_type in ['image', 'video', 'document']:
            file_received = request.FILES.get('file')
            content = request.data.get('content')
            temp_misc_file_path = None 

            try:
                if file_received:
                    file_name = file_received.name
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as temp_file:
                        for chunk in file_received.chunks():
                            temp_file.write(chunk)
                        temp_misc_file_path = temp_file.name 
                    
                    print(f"Arquivo '{file_name}' ({message_type}) recebido e salvo temporariamente: {temp_misc_file_path}")
                    return Response(
                        {'status': 'success', 'type': message_type, 'message': f'{message_type.capitalize()} recebido com sucesso!', 'filename': file_name},
                        status=status.HTTP_200_OK
                    )
                elif content:
                    print(f"Mensagem de {message_type} recebida com conteúdo (provavelmente base64 ou URL).")
                    return Response(
                        {'status': 'success', 'type': message_type, 'message': f'{message_type.capitalize()} recebido com conteúdo.'},
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {'status': 'error', 'message': f'Conteúdo de {message_type} não fornecido.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            finally:
                if temp_misc_file_path and os.path.exists(temp_misc_file_path):
                    os.remove(temp_misc_file_path)
                    print(f"Arquivo temporário misc excluído: {temp_misc_file_path}")


        else:
            return Response(
                {'status': 'error', 'message': f'Tipo de mensagem "{message_type}" não suportado ou reconhecido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        print(f"Erro inesperado no handle_whatsapp_message (fora dos blocos de tipo de mensagem): {e}")
        return Response(
            {'status': 'error', 'message': f'Ocorreu um erro interno: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        # --- Limpeza de TODOS os arquivos temporários DE ÁUDIO ---
        if temp_input_audio_path and os.path.exists(temp_input_audio_path):
            os.remove(temp_input_audio_path)
            print(f"Arquivo temporário excluído (finalmente): {temp_input_audio_path}")
        if temp_wav_path and os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
            print(f"Arquivo temporário excluído (finalmente): {temp_wav_path}")
        if temp_response_ogg_path and os.path.exists(temp_response_ogg_path):
            os.remove(temp_response_ogg_path)
            print(f"Arquivo temporário excluído (finalmente): {temp_response_ogg_path}")
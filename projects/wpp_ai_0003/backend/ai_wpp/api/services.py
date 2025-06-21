# backend/ai_wpp/api/services.py
import openai
import os
import json
from collections import deque
from django.conf import settings
import time # Para simular 'lastActivity' como no JS

class OpenAIService:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL # Ex: 'gpt-4o-mini'
        self.max_tokens = int(settings.OPENAI_MAX_TOKENS) # Convertendo para int
        self.temperature = float(settings.OPENAI_TEMPERATURE) # Convertendo para float
        self.max_history_turns = int(settings.OPENAI_MAX_HISTORY_TURNS) # Convertendo para int

        # Histórico de conversas: {user_id (int): {deque: [], last_activity: timestamp}}
        # Alteramos a estrutura para incluir o timestamp da última atividade.
        self._conversation_history = {} 

    def _get_conversation_data(self, user_id: int):
        """Retorna os dados do histórico para um user_id específico, inicializando se necessário."""
        # Garante que a chave é int, já que user_id é passado como int
        key_user_id = int(user_id) 

        if key_user_id not in self._conversation_history:
            self._conversation_history[key_user_id] = {
                'deque': deque(maxlen=self.max_history_turns * 2), # Armazena pares user/assistant
                'last_activity': time.time()
            }
        
        # Atualiza o timestamp da última atividade a cada acesso
        self._conversation_history[key_user_id]['last_activity'] = time.time()
        return self._conversation_history[key_user_id]['deque']

    def _trim_message(self, message: str, max_len: int) -> str:
        """Limita o tamanho da mensagem para economizar tokens."""
        if len(message) > max_len:
            return message[:max_len] + '...'
        return message

    def _trim_response_by_words(self, text: str, max_words: int = 50) -> str:
        """Garante que a resposta não exceda um número de palavras."""
        words = text.split(' ')
        if len(words) > max_words:
            return ' '.join(words[:max_words]) + '...'
        return text

    def get_chat_response(self, user_id: int, user_message: str) -> str:
        # Acessa a deque do histórico do usuário
        conversation_deque = self._get_conversation_data(user_id)

        # Limitar tamanho da mensagem do usuário para economizar tokens (200 caracteres como no JS)
        trimmed_user_message = self._trim_message(user_message, 200)
        conversation_deque.append({"role": "user", "content": trimmed_user_message})

        # Preparar mensagens para a API da OpenAI
        # A mensagem do sistema deve ser a primeira
        messages_for_openai = [
            {"role": "system", "content": "Você é o Guri Virtual, um assistente de IA do WhatsApp. Responda de forma MUITO CONCISA em no máximo 50 palavras. Seja direto, útil e use emojis moderadamente. Evite explicações longas. Se apresente apenas na primeira mensagem."}
        ]
        
        # Adicionar histórico da conversa de forma segura, garantindo que 'role' e 'content' são strings
        # A deque já tem o maxlen, então apenas precisamos garantir os tipos.
        # Iterar sobre list(conversation_deque) para evitar modificar durante a iteração se necessário
        for msg_item in list(conversation_deque): 
            if isinstance(msg_item, dict) and 'role' in msg_item and 'content' in msg_item:
                try:
                    role = str(msg_item['role'])
                    content = str(msg_item['content'])
                    messages_for_openai.append({"role": role, "content": content})
                except Exception as e:
                    print(f"AVISO: Erro ao converter item de histórico para string: {msg_item} - {e}. Item ignorado.")
            else:
                print(f"AVISO: Item de histórico inválido (não é dict ou falta chaves 'role'/'content'): {msg_item}. Item ignorado.")

        try:
            chat_completion = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages_for_openai,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            ai_message = chat_completion.choices[0].message.content
            final_ai_message = self._trim_response_by_words(ai_message, 50) # Trim por 50 palavras

            # Adicionar resposta do assistente ao histórico
            conversation_deque.append({"role": "assistant", "content": str(final_ai_message)})

            return final_ai_message

        except openai.APICallError as e:
            print(f"Erro na API da OpenAI: {e.status_code} - {e.response.json()}")
            if e.status_code == 401:
                return '🔑 Erro de autenticação com a OpenAI. Verifique a chave de API no servidor.'
            elif e.status_code == 429:
                return '⏰ Limite de requisições da OpenAI excedido. Tente novamente em alguns minutos.'
            elif e.status_code == 400:
                return '❌ Erro na requisição à OpenAI. Reformule sua mensagem.'
            return '🤖 Ocorreu um erro interno na IA. Tente novamente mais tarde.'
        except Exception as e:
            print(f"Erro inesperado ao chamar OpenAI: {e}")
            return '🤖 Ocorreu um erro inesperado na IA. Por favor, tente novamente.'

    def clear_history(self, user_id: int):
        """Limpa o histórico de conversas para um usuário específico."""
        key_user_id = int(user_id) # Garante que a chave é int
        if key_user_id in self._conversation_history:
            del self._conversation_history[key_user_id]
            return True
        return False

    def cleanup_history(self):
        """Limpa conversas inativas (similar ao JS, mas aqui em Python/Django)."""
        # Em um ambiente Django real, isso seria um Cron Job, Celery Task, ou algo agendado.
        # Aqui, é apenas uma demonstração de como a lógica de limpeza funcionaria.
        # A limpeza automática de 2 horas (7200 segundos) conforme o seu JS (120 min = 2 horas)
        two_hours_ago = time.time() - (2 * 60 * 60) 
        
        users_to_delete = []
        for user_id, data in self._conversation_history.items():
            if data['last_activity'] < two_hours_ago:
                users_to_delete.append(user_id)
        
        for user_id in users_to_delete:
            del self._conversation_history[user_id]
            print(f"🧹 Histórico limpo automaticamente para usuário: {user_id}")

# Instancie o serviço OpenAI para ser usado em suas views
# Em um ambiente de produção, considere usar um Singleton ou injeção de dependência.
# Para este exemplo simples, instanciar uma vez e reusar é OK.
openai_service = OpenAIService()

# Para fins de demonstração, você pode chamar cleanup_history periodicamente
# MAS: Em um app Django real, você NÃO faria isso diretamente aqui.
# Isso deve ser agendado por um scheduler (ex: Celery Beat, cron job no servidor).
# Por exemplo:
# from django.utils import autoreload
# if settings.DEBUG and os.environ.get('RUN_MAIN') == 'true': # Garante que roda apenas uma vez no ambiente de dev
#     def run_cleanup():
#         # print("Executando cleanup_history...")
#         openai_service.cleanup_history()
#     # Agendar para rodar a cada 30 minutos (1800 segundos)
#     # Nao use isto em producao!
#     import threading
#     cleanup_thread = threading.Timer(1800.0, run_cleanup) 
#     cleanup_thread.daemon = True # Permite que o thread termine com o programa principal
#     cleanup_thread.start()
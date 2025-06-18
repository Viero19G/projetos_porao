import openai
import os
from django.conf import settings
from .models import Conversation, Message

class AIAgent:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        
    def process_message(self, conversation, message_content, message_type='text', media_file=None):
        """
        Process incoming message and generate AI response
        """
        try:
            # Get conversation history
            history = self.get_conversation_history(conversation)
            
            # Prepare prompt based on message type
            if message_type == 'text':
                user_message = message_content
            elif message_type == 'image':
                user_message = f"[Imagem enviada] {message_content}" if message_content else "[Imagem enviada]"
            elif message_type == 'audio':
                user_message = f"[Áudio enviado] {message_content}" if message_content else "[Áudio enviado]"
            elif message_type == 'video':
                user_message = f"[Vídeo enviado] {message_content}" if message_content else "[Vídeo enviado]"
            elif message_type == 'document':
                user_message = f"[Documento enviado] {message_content}" if message_content else "[Documento enviado]"
            else:
                user_message = f"[{message_type}] {message_content}" if message_content else f"[{message_type}]"
            
            # Save user message
            Message.objects.create(
                conversation=conversation,
                sender_type='user',
                message_type=message_type,
                content=user_message,
                media_file=media_file
            )
            
            # Generate AI response
            ai_response = self.generate_response(history + [user_message])
            
            # Save AI response
            ai_message = Message.objects.create(
                conversation=conversation,
                sender_type='ai',
                message_type='text',
                content=ai_response
            )
            
            # Update conversation history file
            self.update_conversation_file(conversation)
            
            return ai_response
            
        except Exception as e:
            print(f"Erro no AI Agent: {e}")
            return "Desculpe, houve um erro ao processar sua mensagem. Tente novamente."
    
    def get_conversation_history(self, conversation, limit=20):
        """
        Get recent conversation history
        """
        messages = Message.objects.filter(
            conversation=conversation
        ).order_by('-timestamp')[:limit]
        
        history = []
        for message in reversed(messages):
            prefix = "Usuário" if message.sender_type == 'user' else "IA"
            history.append(f"{prefix}: {message.content}")
        
        return history
    
    def generate_response(self, conversation_history):
        """
        Generate AI response using OpenAI or fallback to simple responses
        """
        if not settings.OPENAI_API_KEY:
            return self.simple_response(conversation_history)
        
        try:
            # Prepare messages for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": """Você é um assistente útil e amigável no WhatsApp. 
                    Responda de forma natural, conversacional e em português.
                    Seja conciso mas informativo. Mantenha um tom amigável e profissional."""
                }
            ]
            
            # Add conversation history
            for i, msg in enumerate(conversation_history[-10:]):  # Last 10 messages
                if msg.startswith("Usuário:"):
                    messages.append({"role": "user", "content": msg[8:]})
                elif msg.startswith("IA:"):
                    messages.append({"role": "assistant", "content": msg[3:]})
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Erro na API OpenAI: {e}")
            return self.simple_response(conversation_history)
    
    def simple_response(self, conversation_history):
        """
        Simple fallback responses when OpenAI is not available
        """
        last_message = conversation_history[-1] if conversation_history else ""
        
        if "olá" in last_message.lower() or "oi" in last_message.lower():
            return "Olá! Como posso ajudá-lo hoje?"
        elif "como você está" in last_message.lower():
            return "Estou bem, obrigado por perguntar! Como posso ajudá-lo?"
        elif "obrigado" in last_message.lower():
            return "De nada! Fico feliz em ajudar. Há mais alguma coisa que posso fazer por você?"
        elif "[Imagem enviada]" in last_message:
            return "Recebi sua imagem! Infelizmente ainda não posso processar imagens, mas posso ajudá-lo de outras formas."
        elif "[Áudio enviado]" in last_message:
            return "Recebi seu áudio! Infelizmente ainda não posso processar áudios, mas posso ajudá-lo por texto."
        elif "[Vídeo enviado]" in last_message:
            return "Recebi seu vídeo! Infelizmente ainda não posso processar vídeos, mas posso ajudá-lo de outras formas."
        elif "[Documento enviado]" in last_message:
            return "Recebi seu documento! Infelizmente ainda não posso processar documentos, mas posso ajudá-lo de outras formas."
        else:
            return "Obrigado pela sua mensagem! Como posso ajudá-lo?"
    
    def update_conversation_file(self, conversation):
        """
        Update conversation history in text file
        """
        try:
            file_path = os.path.join(
                settings.CONVERSATIONS_DIR, 
                f"conversation_{conversation.contact.phone_number}.txt"
            )
            
            messages = Message.objects.filter(
                conversation=conversation
            ).order_by('timestamp')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Conversa com: {conversation.contact.name} ({conversation.contact.phone_number})\n")
                f.write(f"Iniciada em: {conversation.created_at}\n")
                f.write("=" * 50 + "\n\n")
                
                for message in messages:
                    timestamp = message.timestamp.strftime("%d/%m/%Y %H:%M:%S")
                    sender = "Usuário" if message.sender_type == 'user' else "IA"
                    f.write(f"[{timestamp}] {sender}: {message.content}\n")
                    
                    if message.media_file:
                        f.write(f"    📎 Arquivo: {message.media_file.name}\n")
                    f.write("\n")
        
        except Exception as e:
            print(f"Erro ao atualizar arquivo de conversa: {e}")
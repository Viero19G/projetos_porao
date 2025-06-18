from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Contact, Conversation, Message
from .ai_agent import AIAgent
import json

@api_view(['POST'])
@permission_classes([AllowAny])  # Remove for production, add proper authentication
def process_message(request):
    """
    Process incoming WhatsApp message and return AI response
    """
    try:
        # Extract message data
        phone_number = request.data.get('phone_number')
        contact_name = request.data.get('contact_name', 'Unknown')
        message_type = request.data.get('message_type', 'text')
        message_body = request.data.get('message_body', '')
        has_media = request.data.get('has_media', False)
        media_file = request.FILES.get('media_file')
        
        if not phone_number:
            return Response(
                {'error': 'phone_number is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create contact
        contact, created = Contact.objects.get_or_create(
            phone_number=phone_number,
            defaults={'name': contact_name}
        )
        
        # Update contact name if provided and different
        if contact_name and contact_name != 'Unknown' and contact.name != contact_name:
            contact.name = contact_name
            contact.save()
        
        # Get or create conversation
        conversation, created = Conversation.objects.get_or_create(
            contact=contact
        )
        
        # Initialize AI Agent
        ai_agent = AIAgent()
        
        # Process message with AI
        ai_response = ai_agent.process_message(
            conversation=conversation,
            message_content=message_body,
            message_type=message_type,
            media_file=media_file
        )
        
        response_data = {
            'success': True,
            'response': ai_response,
            'contact_id': contact.id,
            'conversation_id': conversation.id
        }
        
        # Handle media response if needed (placeholder for future implementation)
        # response_data['media_response'] = None
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Internal server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_conversation_history(request, phone_number):
    """
    Get conversation history for a specific phone number
    """
    try:
        contact = Contact.objects.get(phone_number=phone_number)
        conversation = Conversation.objects.get(contact=contact)
        
        messages = Message.objects.filter(
            conversation=conversation
        ).order_by('timestamp')
        
        history = []
        for message in messages:
            history.append({
                'id': message.id,
                'sender_type': message.sender_type,
                'message_type': message.message_type,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'has_media': bool(message.media_file)
            })
        
        return Response({
            'contact': {
                'phone_number': contact.phone_number,
                'name': contact.name
            },
            'messages': history
        })
        
    except Contact.DoesNotExist:
        return Response(
            {'error': 'Contact not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Conversation.DoesNotExist:
        return Response(
            {'error': 'Conversation not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint
    """
    return Response({'status': 'ok', 'service': 'WhatsApp AI API'})
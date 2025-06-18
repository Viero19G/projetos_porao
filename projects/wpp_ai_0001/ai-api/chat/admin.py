from django.contrib import admin
from .models import Contact, Conversation, Message

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'name', 'created_at')
    search_fields = ('phone_number', 'name')
    list_filter = ('created_at',)

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('contact', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('contact__phone_number', 'contact__name')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender_type', 'message_type', 'timestamp')
    list_filter = ('sender_type', 'message_type', 'timestamp')
    search_fields = ('content', 'conversation__contact__phone_number')
    readonly_fields = ('timestamp',)
"""In-App Chat Models - Text, Photos, Files, Voice Messages"""

from django.db import models
from django.conf import settings
from floor_app.core.models import AuditMixin


class ChatRoom(AuditMixin):
    ROOM_TYPES = (
        ('DIRECT', 'Direct Message'),
        ('GROUP', 'Group Chat'),
        ('CHANNEL', 'Channel'),
    )

    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='chat_rooms/', null=True, blank=True)

    # Participants
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_rooms')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_chats')

    # Settings
    is_archived = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)

    # For direct messages (2 participants)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'chat_rooms'
        ordering = ['-last_message_at']

    def __str__(self):
        return self.name or f"{self.get_room_type_display()} Room"


class ChatMessage(AuditMixin):
    MESSAGE_TYPES = (
        ('TEXT', 'Text'),
        ('PHOTO', 'Photo'),
        ('FILE', 'File'),
        ('VOICE', 'Voice Message'),
        ('SYSTEM', 'System Message'),
    )

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='TEXT')

    # Content
    text = models.TextField(blank=True)
    photo = models.ImageField(upload_to='chat_photos/%Y/%m/%d/', null=True, blank=True)
    file = models.FileField(upload_to='chat_files/%Y/%m/%d/', null=True, blank=True)
    voice = models.FileField(upload_to='chat_voice/%Y/%m/%d/', null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    voice_duration_seconds = models.IntegerField(null=True, blank=True)

    # Reply/Thread
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    # Status
    sent_at = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['sent_at']

    def __str__(self):
        return f"{self.sender.get_full_name()}: {self.text[:50]}"


class MessageRead(AuditMixin):
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='read_messages')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'message_read_receipts'
        unique_together = [['message', 'user']]

    def __str__(self):
        return f"{self.user.get_full_name()} read {self.message.id}"


class ChatNotification(AuditMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_notifications')
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='notifications')
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='notifications')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'chat_notifications'
        ordering = ['-created_at']

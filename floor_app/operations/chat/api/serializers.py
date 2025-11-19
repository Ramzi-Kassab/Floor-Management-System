"""Chat API Serializers"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import ChatRoom, ChatMessage, MessageRead, ChatNotification

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for chat"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email']
        read_only_fields = fields


class MessageReadSerializer(serializers.ModelSerializer):
    """Message read receipt serializer"""
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = MessageRead
        fields = ['id', 'user', 'read_at']
        read_only_fields = fields


class ChatMessageSerializer(serializers.ModelSerializer):
    """Chat message serializer"""
    sender = UserBasicSerializer(read_only=True)
    reply_to = serializers.SerializerMethodField()
    read_receipts = MessageReadSerializer(many=True, read_only=True)
    read_count = serializers.IntegerField(source='read_receipts.count', read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'room', 'sender', 'message_type', 'text', 'photo', 'file',
            'voice', 'file_name', 'file_size', 'voice_duration_seconds',
            'reply_to', 'sent_at', 'is_edited', 'edited_at', 'is_deleted',
            'deleted_at', 'read_receipts', 'read_count', 'created_at'
        ]
        read_only_fields = [
            'id', 'sender', 'sent_at', 'is_edited', 'edited_at',
            'is_deleted', 'deleted_at', 'read_receipts', 'read_count', 'created_at'
        ]

    def get_reply_to(self, obj):
        """Get simplified reply_to message"""
        if obj.reply_to:
            return {
                'id': obj.reply_to.id,
                'sender_name': obj.reply_to.sender.get_full_name(),
                'text': obj.reply_to.text[:100],
                'message_type': obj.reply_to.message_type
            }
        return None


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages"""

    class Meta:
        model = ChatMessage
        fields = [
            'room', 'message_type', 'text', 'photo', 'file', 'voice',
            'file_name', 'file_size', 'voice_duration_seconds', 'reply_to'
        ]

    def validate(self, data):
        """Validate message content based on type"""
        message_type = data.get('message_type', 'TEXT')

        if message_type == 'TEXT' and not data.get('text'):
            raise serializers.ValidationError("Text is required for TEXT messages")

        if message_type == 'PHOTO' and not data.get('photo'):
            raise serializers.ValidationError("Photo is required for PHOTO messages")

        if message_type == 'FILE' and not data.get('file'):
            raise serializers.ValidationError("File is required for FILE messages")

        if message_type == 'VOICE' and not data.get('voice'):
            raise serializers.ValidationError("Voice file is required for VOICE messages")

        return data


class ChatRoomSerializer(serializers.ModelSerializer):
    """Chat room serializer"""
    participants = UserBasicSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    created_by = UserBasicSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.IntegerField(read_only=True, required=False)
    participant_count = serializers.IntegerField(
        source='participants.count',
        read_only=True
    )

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_type', 'name', 'description', 'photo', 'participants',
            'participant_ids', 'created_by', 'is_archived', 'is_muted',
            'last_message_at', 'last_message', 'unread_count', 'participant_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'last_message_at', 'last_message',
            'unread_count', 'participant_count', 'created_at', 'updated_at'
        ]

    def get_last_message(self, obj):
        """Get the last message in the room"""
        last_msg = obj.messages.filter(is_deleted=False).order_by('-sent_at').first()
        if last_msg:
            return {
                'id': last_msg.id,
                'sender_name': last_msg.sender.get_full_name(),
                'text': last_msg.text[:100] if last_msg.text else '',
                'message_type': last_msg.message_type,
                'sent_at': last_msg.sent_at
            }
        return None


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat rooms"""
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = ChatRoom
        fields = [
            'room_type', 'name', 'description', 'photo', 'participant_ids'
        ]

    def validate(self, data):
        """Validate room creation"""
        room_type = data.get('room_type')

        if room_type == 'GROUP' and not data.get('name'):
            raise serializers.ValidationError("Name is required for group chats")

        if room_type == 'CHANNEL' and not data.get('name'):
            raise serializers.ValidationError("Name is required for channels")

        if room_type == 'DIRECT':
            participant_ids = data.get('participant_ids', [])
            if len(participant_ids) != 1:
                raise serializers.ValidationError(
                    "Direct messages require exactly 1 other participant"
                )

        return data


class ChatNotificationSerializer(serializers.ModelSerializer):
    """Chat notification serializer"""
    room = ChatRoomSerializer(read_only=True)
    message = ChatMessageSerializer(read_only=True)

    class Meta:
        model = ChatNotification
        fields = [
            'id', 'user', 'room', 'message', 'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = fields


class EditMessageSerializer(serializers.Serializer):
    """Serializer for editing messages"""
    text = serializers.CharField(required=True)


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking messages as read"""
    up_to_message_id = serializers.IntegerField(required=False)


class AddParticipantsSerializer(serializers.Serializer):
    """Serializer for adding participants"""
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )


class SearchMessagesSerializer(serializers.Serializer):
    """Serializer for searching messages"""
    query = serializers.CharField(required=True, min_length=2)

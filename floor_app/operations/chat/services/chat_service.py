"""Chat Service - Business Logic for In-App Chat System"""

from typing import Dict, List, Any, Optional
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Max
from ..models import ChatRoom, ChatMessage, MessageRead, ChatNotification

User = get_user_model()


class ChatService:
    """Service for managing in-app chat functionality"""

    @classmethod
    @transaction.atomic
    def create_direct_chat(cls, user1: User, user2: User) -> ChatRoom:
        """Create or get existing direct message room between two users"""
        # Check if direct chat already exists
        existing_room = ChatRoom.objects.filter(
            room_type='DIRECT',
            participants=user1
        ).filter(
            participants=user2
        ).first()

        if existing_room:
            return existing_room

        # Create new direct chat
        room = ChatRoom.objects.create(
            room_type='DIRECT',
            created_by=user1
        )
        room.participants.add(user1, user2)
        return room

    @classmethod
    @transaction.atomic
    def create_group_chat(cls, creator: User, name: str, participant_ids: List[int],
                         description: str = '', photo=None) -> ChatRoom:
        """Create a group chat room"""
        room = ChatRoom.objects.create(
            room_type='GROUP',
            name=name,
            description=description,
            photo=photo,
            created_by=creator
        )

        # Add creator and participants
        room.participants.add(creator)
        if participant_ids:
            room.participants.add(*participant_ids)

        # Send system message
        cls.send_system_message(
            room=room,
            text=f"{creator.get_full_name()} created the group"
        )

        return room

    @classmethod
    @transaction.atomic
    def create_channel(cls, creator: User, name: str, description: str = '',
                      photo=None) -> ChatRoom:
        """Create a broadcast channel"""
        room = ChatRoom.objects.create(
            room_type='CHANNEL',
            name=name,
            description=description,
            photo=photo,
            created_by=creator
        )
        room.participants.add(creator)

        cls.send_system_message(
            room=room,
            text=f"Channel created by {creator.get_full_name()}"
        )

        return room

    @classmethod
    @transaction.atomic
    def send_message(cls, room: ChatRoom, sender: User, message_type: str,
                    text: str = '', photo=None, file=None, voice=None,
                    file_name: str = '', file_size: int = None,
                    voice_duration: int = None, reply_to_id: int = None) -> ChatMessage:
        """Send a message in a chat room"""
        # Verify sender is participant
        if not room.participants.filter(id=sender.id).exists():
            raise ValueError("Sender is not a participant in this room")

        message = ChatMessage.objects.create(
            room=room,
            sender=sender,
            message_type=message_type,
            text=text,
            photo=photo,
            file=file,
            voice=voice,
            file_name=file_name,
            file_size=file_size,
            voice_duration_seconds=voice_duration,
            reply_to_id=reply_to_id
        )

        # Update room's last message time
        room.last_message_at = message.sent_at
        room.save(update_fields=['last_message_at'])

        # Create notifications for other participants
        cls._create_notifications(message)

        return message

    @classmethod
    def send_system_message(cls, room: ChatRoom, text: str) -> ChatMessage:
        """Send a system message (no sender)"""
        message = ChatMessage.objects.create(
            room=room,
            sender=room.created_by,  # Use room creator as sender for system messages
            message_type='SYSTEM',
            text=text
        )
        return message

    @classmethod
    @transaction.atomic
    def edit_message(cls, message: ChatMessage, new_text: str, editor: User) -> ChatMessage:
        """Edit a text message"""
        if message.sender != editor:
            raise ValueError("Only message sender can edit the message")

        if message.message_type != 'TEXT':
            raise ValueError("Only text messages can be edited")

        message.text = new_text
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save(update_fields=['text', 'is_edited', 'edited_at'])

        return message

    @classmethod
    @transaction.atomic
    def delete_message(cls, message: ChatMessage, deleter: User) -> ChatMessage:
        """Soft delete a message"""
        if message.sender != deleter:
            raise ValueError("Only message sender can delete the message")

        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.save(update_fields=['is_deleted', 'deleted_at'])

        return message

    @classmethod
    @transaction.atomic
    def mark_messages_as_read(cls, room: ChatRoom, user: User,
                             up_to_message_id: int = None) -> int:
        """Mark messages as read for a user"""
        messages_query = ChatMessage.objects.filter(
            room=room,
            is_deleted=False
        ).exclude(sender=user)

        if up_to_message_id:
            messages_query = messages_query.filter(id__lte=up_to_message_id)

        count = 0
        for message in messages_query:
            _, created = MessageRead.objects.get_or_create(
                message=message,
                user=user
            )
            if created:
                count += 1

        # Mark notifications as read
        ChatNotification.objects.filter(
            room=room,
            user=user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

        return count

    @classmethod
    def get_unread_count(cls, room: ChatRoom, user: User) -> int:
        """Get count of unread messages for a user in a room"""
        return ChatMessage.objects.filter(
            room=room,
            is_deleted=False
        ).exclude(sender=user).exclude(
            read_receipts__user=user
        ).count()

    @classmethod
    def get_chat_history(cls, room: ChatRoom, user: User, limit: int = 50,
                        before_message_id: int = None) -> List[ChatMessage]:
        """Get paginated chat history"""
        # Verify user is participant
        if not room.participants.filter(id=user.id).exists():
            raise ValueError("User is not a participant in this room")

        messages = ChatMessage.objects.filter(
            room=room,
            is_deleted=False
        ).select_related('sender', 'reply_to').prefetch_related('read_receipts')

        if before_message_id:
            messages = messages.filter(id__lt=before_message_id)

        return list(messages.order_by('-sent_at')[:limit])

    @classmethod
    def get_user_rooms(cls, user: User) -> List[ChatRoom]:
        """Get all chat rooms for a user"""
        return list(
            ChatRoom.objects.filter(
                participants=user,
                is_archived=False
            ).annotate(
                unread_count=Count(
                    'messages',
                    filter=Q(messages__is_deleted=False) &
                           ~Q(messages__sender=user) &
                           ~Q(messages__read_receipts__user=user)
                )
            ).order_by('-last_message_at')
        )

    @classmethod
    @transaction.atomic
    def add_participants(cls, room: ChatRoom, adder: User,
                        participant_ids: List[int]) -> ChatRoom:
        """Add participants to group chat or channel"""
        if room.room_type == 'DIRECT':
            raise ValueError("Cannot add participants to direct messages")

        if not room.participants.filter(id=adder.id).exists():
            raise ValueError("Only participants can add others")

        # Add participants
        room.participants.add(*participant_ids)

        # Send system message
        added_users = User.objects.filter(id__in=participant_ids)
        names = ', '.join([u.get_full_name() for u in added_users])
        cls.send_system_message(
            room=room,
            text=f"{adder.get_full_name()} added {names}"
        )

        return room

    @classmethod
    @transaction.atomic
    def remove_participant(cls, room: ChatRoom, remover: User, user_id: int) -> ChatRoom:
        """Remove a participant from group chat"""
        if room.room_type == 'DIRECT':
            raise ValueError("Cannot remove participants from direct messages")

        if remover.id != room.created_by_id and remover.id != user_id:
            raise ValueError("Only group creator or the user themselves can remove")

        user_to_remove = User.objects.get(id=user_id)
        room.participants.remove(user_to_remove)

        # Send system message
        cls.send_system_message(
            room=room,
            text=f"{user_to_remove.get_full_name()} left the group"
        )

        return room

    @classmethod
    @transaction.atomic
    def archive_room(cls, room: ChatRoom, user: User) -> ChatRoom:
        """Archive a chat room for a user"""
        room.is_archived = True
        room.save(update_fields=['is_archived'])
        return room

    @classmethod
    @transaction.atomic
    def mute_room(cls, room: ChatRoom, user: User) -> ChatRoom:
        """Mute notifications for a room"""
        room.is_muted = True
        room.save(update_fields=['is_muted'])
        return room

    @classmethod
    def get_unread_notifications_count(cls, user: User) -> int:
        """Get total unread notifications count for user"""
        return ChatNotification.objects.filter(
            user=user,
            is_read=False
        ).count()

    @classmethod
    def _create_notifications(cls, message: ChatMessage) -> None:
        """Create notifications for message recipients"""
        # Get all participants except sender
        recipients = message.room.participants.exclude(id=message.sender_id)

        # Skip if room is muted
        if message.room.is_muted:
            return

        notifications = [
            ChatNotification(
                user=recipient,
                room=message.room,
                message=message
            )
            for recipient in recipients
        ]
        ChatNotification.objects.bulk_create(notifications)

    @classmethod
    def search_messages(cls, room: ChatRoom, user: User, query: str) -> List[ChatMessage]:
        """Search messages in a room"""
        if not room.participants.filter(id=user.id).exists():
            raise ValueError("User is not a participant in this room")

        return list(
            ChatMessage.objects.filter(
                room=room,
                is_deleted=False,
                message_type='TEXT',
                text__icontains=query
            ).select_related('sender').order_by('-sent_at')[:50]
        )

    @classmethod
    def get_room_statistics(cls, room: ChatRoom) -> Dict[str, Any]:
        """Get statistics for a chat room"""
        total_messages = ChatMessage.objects.filter(room=room, is_deleted=False).count()

        message_breakdown = ChatMessage.objects.filter(
            room=room,
            is_deleted=False
        ).values('message_type').annotate(count=Count('id'))

        top_contributors = ChatMessage.objects.filter(
            room=room,
            is_deleted=False
        ).values(
            'sender__first_name',
            'sender__last_name'
        ).annotate(
            message_count=Count('id')
        ).order_by('-message_count')[:5]

        return {
            'total_messages': total_messages,
            'total_participants': room.participants.count(),
            'message_breakdown': list(message_breakdown),
            'top_contributors': list(top_contributors),
            'created_at': room.created_at,
            'last_message_at': room.last_message_at,
        }

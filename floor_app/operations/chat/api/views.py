"""Chat API Views"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..models import ChatRoom, ChatMessage, ChatNotification
from ..services.chat_service import ChatService
from .serializers import (
    ChatRoomSerializer, ChatRoomCreateSerializer, ChatMessageSerializer,
    ChatMessageCreateSerializer, ChatNotificationSerializer, EditMessageSerializer,
    MarkAsReadSerializer, AddParticipantsSerializer, SearchMessagesSerializer
)


class ChatRoomViewSet(viewsets.ModelViewSet):
    """Chat room management"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ChatRoomCreateSerializer
        return ChatRoomSerializer

    def get_queryset(self):
        """Get rooms where user is participant"""
        return ChatRoom.objects.filter(
            participants=self.request.user,
            is_archived=False
        ).order_by('-last_message_at')

    def create(self, request):
        """Create a new chat room"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        room_type = serializer.validated_data['room_type']
        participant_ids = serializer.validated_data.get('participant_ids', [])

        try:
            if room_type == 'DIRECT':
                # Create direct message
                other_user_id = participant_ids[0]
                from django.contrib.auth import get_user_model
                User = get_user_model()
                other_user = get_object_or_404(User, id=other_user_id)
                room = ChatService.create_direct_chat(request.user, other_user)

            elif room_type == 'GROUP':
                # Create group chat
                room = ChatService.create_group_chat(
                    creator=request.user,
                    name=serializer.validated_data['name'],
                    participant_ids=participant_ids,
                    description=serializer.validated_data.get('description', ''),
                    photo=serializer.validated_data.get('photo')
                )

            elif room_type == 'CHANNEL':
                # Create channel
                room = ChatService.create_channel(
                    creator=request.user,
                    name=serializer.validated_data['name'],
                    description=serializer.validated_data.get('description', ''),
                    photo=serializer.validated_data.get('photo')
                )

            else:
                return Response(
                    {'error': 'Invalid room type'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                ChatRoomSerializer(room).data,
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_participants(self, request, pk=None):
        """Add participants to group/channel"""
        room = self.get_object()
        serializer = AddParticipantsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            room = ChatService.add_participants(
                room=room,
                adder=request.user,
                participant_ids=serializer.validated_data['participant_ids']
            )
            return Response(ChatRoomSerializer(room).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """Remove a participant from group"""
        room = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            room = ChatService.remove_participant(
                room=room,
                remover=request.user,
                user_id=user_id
            )
            return Response(ChatRoomSerializer(room).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a chat room"""
        room = self.get_object()
        room = ChatService.archive_room(room, request.user)
        return Response({'status': 'archived'})

    @action(detail=True, methods=['post'])
    def mute(self, request, pk=None):
        """Mute notifications for a room"""
        room = self.get_object()
        room = ChatService.mute_room(room, request.user)
        return Response({'status': 'muted'})

    @action(detail=True, methods=['post'])
    def unmute(self, request, pk=None):
        """Unmute notifications for a room"""
        room = self.get_object()
        room.is_muted = False
        room.save(update_fields=['is_muted'])
        return Response({'status': 'unmuted'})

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get room statistics"""
        room = self.get_object()
        stats = ChatService.get_room_statistics(room)
        return Response(stats)


class ChatMessageViewSet(viewsets.ModelViewSet):
    """Chat message management"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ChatMessageCreateSerializer
        return ChatMessageSerializer

    def get_queryset(self):
        """Get messages from rooms where user is participant"""
        room_id = self.request.query_params.get('room_id')

        queryset = ChatMessage.objects.filter(
            room__participants=self.request.user,
            is_deleted=False
        ).select_related('sender', 'reply_to').prefetch_related('read_receipts')

        if room_id:
            queryset = queryset.filter(room_id=room_id)

        return queryset.order_by('-sent_at')

    def create(self, request):
        """Send a message"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            room = get_object_or_404(ChatRoom, id=serializer.validated_data['room'].id)

            message = ChatService.send_message(
                room=room,
                sender=request.user,
                message_type=serializer.validated_data['message_type'],
                text=serializer.validated_data.get('text', ''),
                photo=serializer.validated_data.get('photo'),
                file=serializer.validated_data.get('file'),
                voice=serializer.validated_data.get('voice'),
                file_name=serializer.validated_data.get('file_name', ''),
                file_size=serializer.validated_data.get('file_size'),
                voice_duration=serializer.validated_data.get('voice_duration_seconds'),
                reply_to_id=serializer.validated_data.get('reply_to_id')
            )

            return Response(
                ChatMessageSerializer(message).data,
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def edit(self, request, pk=None):
        """Edit a text message"""
        message = self.get_object()
        serializer = EditMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            message = ChatService.edit_message(
                message=message,
                new_text=serializer.validated_data['text'],
                editor=request.user
            )
            return Response(ChatMessageSerializer(message).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def delete(self, request, pk=None):
        """Delete a message"""
        message = self.get_object()

        try:
            message = ChatService.delete_message(message, request.user)
            return Response({'status': 'deleted'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def mark_as_read(self, request):
        """Mark messages as read in a room"""
        room_id = request.data.get('room_id')

        if not room_id:
            return Response(
                {'error': 'room_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        room = get_object_or_404(ChatRoom, id=room_id)
        serializer = MarkAsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        count = ChatService.mark_messages_as_read(
            room=room,
            user=request.user,
            up_to_message_id=serializer.validated_data.get('up_to_message_id')
        )

        return Response({'marked_read': count})

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get chat history for a room"""
        room_id = request.query_params.get('room_id')
        limit = int(request.query_params.get('limit', 50))
        before_message_id = request.query_params.get('before_message_id')

        if not room_id:
            return Response(
                {'error': 'room_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        room = get_object_or_404(ChatRoom, id=room_id)

        try:
            messages = ChatService.get_chat_history(
                room=room,
                user=request.user,
                limit=limit,
                before_message_id=int(before_message_id) if before_message_id else None
            )

            return Response(ChatMessageSerializer(messages, many=True).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def search(self, request):
        """Search messages in a room"""
        room_id = request.data.get('room_id')

        if not room_id:
            return Response(
                {'error': 'room_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        room = get_object_or_404(ChatRoom, id=room_id)
        serializer = SearchMessagesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            messages = ChatService.search_messages(
                room=room,
                user=request.user,
                query=serializer.validated_data['query']
            )

            return Response(ChatMessageSerializer(messages, many=True).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChatNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Chat notification management"""
    serializer_class = ChatNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get notifications for current user"""
        return ChatNotification.objects.filter(
            user=self.request.user
        ).select_related('room', 'message', 'message__sender').order_by('-created_at')

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = ChatService.get_unread_notifications_count(request.user)
        return Response({'unread_count': count})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        from django.utils import timezone
        count = ChatNotification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

        return Response({'marked_read': count})

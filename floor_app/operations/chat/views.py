"""
In-App Chat System Views

Template-rendering views for chat interface, channels, and direct messages.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Max, Prefetch
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import (
    ChatRoom,
    ChatMessage,
    MessageRead,
    ChatNotification,
)

User = get_user_model()


@login_required
def chat_interface(request):
    """
    Main chat interface.

    Shows:
    - Chat room list
    - Active conversation
    - Message history
    - Send message form
    """
    user = request.user

    try:
        # Get all chat rooms for user
        rooms = ChatRoom.objects.filter(
            participants=user,
            is_archived=False
        ).annotate(
            unread_count=Count(
                'messages',
                filter=~Q(messages__read_receipts__user=user)
            ),
            message_count=Count('messages')
        ).order_by('-last_message_at')

        # Get selected room (from URL parameter or most recent)
        room_id = request.GET.get('room')
        selected_room = None

        if room_id:
            try:
                selected_room = rooms.get(pk=room_id)
            except ChatRoom.DoesNotExist:
                messages.error(request, 'Chat room not found.')

        if not selected_room and rooms.exists():
            selected_room = rooms.first()

        # Get messages for selected room
        room_messages = []
        if selected_room:
            room_messages = ChatMessage.objects.filter(
                room=selected_room,
                is_deleted=False
            ).select_related(
                'sender',
                'reply_to'
            ).prefetch_related(
                'read_receipts'
            ).order_by('sent_at')

            # Mark messages as read
            unread_messages = room_messages.exclude(
                read_receipts__user=user
            ).exclude(sender=user)

            for msg in unread_messages:
                MessageRead.objects.get_or_create(
                    message=msg,
                    user=user
                )

        # Handle send message
        if request.method == 'POST' and selected_room:
            try:
                message_text = request.POST.get('message', '').strip()
                message_type = request.POST.get('message_type', 'TEXT')
                reply_to_id = request.POST.get('reply_to')

                if message_text or message_type != 'TEXT':
                    message = ChatMessage.objects.create(
                        room=selected_room,
                        sender=user,
                        message_type=message_type,
                        text=message_text
                    )

                    if reply_to_id:
                        try:
                            reply_to = ChatMessage.objects.get(pk=reply_to_id)
                            message.reply_to = reply_to
                            message.save()
                        except ChatMessage.DoesNotExist:
                            pass

                    # Update room last message time
                    selected_room.last_message_at = timezone.now()
                    selected_room.save()

                    # Create notifications for other participants
                    for participant in selected_room.participants.exclude(pk=user.pk):
                        ChatNotification.objects.create(
                            user=participant,
                            room=selected_room,
                            message=message
                        )

                    return redirect(f'?room={selected_room.pk}')
                else:
                    messages.warning(request, 'Please enter a message.')

            except Exception as e:
                messages.error(request, f'Error sending message: {str(e)}')

        context = {
            'rooms': rooms,
            'selected_room': selected_room,
            'room_messages': room_messages,
            'page_title': 'Chat',
        }

    except Exception as e:
        messages.error(request, f'Error loading chat: {str(e)}')
        context = {
            'rooms': [],
            'selected_room': None,
            'room_messages': [],
            'page_title': 'Chat',
        }

    return render(request, 'chat/chat_interface.html', context)


@login_required
def channel_list(request):
    """
    List all channels (group chats).

    Shows:
    - Available channels
    - Join/leave options
    - Channel information
    """
    user = request.user

    try:
        # Get all group/channel rooms
        channels = ChatRoom.objects.filter(
            room_type__in=['GROUP', 'CHANNEL']
        ).annotate(
            member_count=Count('participants'),
            message_count=Count('messages')
        ).order_by('-last_message_at')

        # Separate joined and available channels
        joined_channels = channels.filter(participants=user)
        available_channels = channels.exclude(participants=user)

        # Handle join/leave
        if request.method == 'POST':
            action = request.POST.get('action')
            channel_id = request.POST.get('channel_id')

            if channel_id:
                try:
                    channel = ChatRoom.objects.get(pk=channel_id)

                    if action == 'join':
                        channel.participants.add(user)
                        messages.success(request, f'Joined {channel.name}')

                        # Create system message
                        ChatMessage.objects.create(
                            room=channel,
                            sender=user,
                            message_type='SYSTEM',
                            text=f'{user.get_full_name()} joined the channel'
                        )

                    elif action == 'leave':
                        channel.participants.remove(user)
                        messages.success(request, f'Left {channel.name}')

                        # Create system message
                        ChatMessage.objects.create(
                            room=channel,
                            sender=user,
                            message_type='SYSTEM',
                            text=f'{user.get_full_name()} left the channel'
                        )

                    return redirect('chat:channel_list')

                except ChatRoom.DoesNotExist:
                    messages.error(request, 'Channel not found.')
                except Exception as e:
                    messages.error(request, f'Error: {str(e)}')

        context = {
            'joined_channels': joined_channels,
            'available_channels': available_channels,
            'page_title': 'Channels',
        }

    except Exception as e:
        messages.error(request, f'Error loading channels: {str(e)}')
        context = {
            'joined_channels': [],
            'available_channels': [],
            'page_title': 'Channels',
        }

    return render(request, 'chat/channel_list.html', context)


@login_required
def direct_messages(request):
    """
    List all direct message conversations.

    Shows:
    - Active DM conversations
    - Start new conversation
    """
    user = request.user

    try:
        # Get all direct message rooms
        dm_rooms = ChatRoom.objects.filter(
            room_type='DIRECT',
            participants=user
        ).annotate(
            unread_count=Count(
                'messages',
                filter=~Q(messages__read_receipts__user=user)
            )
        ).prefetch_related('participants').order_by('-last_message_at')

        # Get other participant for each DM
        dm_list = []
        for room in dm_rooms:
            other_user = room.participants.exclude(pk=user.pk).first()
            if other_user:
                dm_list.append({
                    'room': room,
                    'other_user': other_user,
                    'unread_count': room.unread_count,
                })

        # Handle create new DM
        if request.method == 'POST':
            try:
                other_user_id = request.POST.get('user_id')
                if other_user_id:
                    other_user = get_object_or_404(User, pk=other_user_id)

                    # Check if DM already exists
                    existing_room = ChatRoom.objects.filter(
                        room_type='DIRECT',
                        participants=user
                    ).filter(participants=other_user).first()

                    if existing_room:
                        return redirect(f'/chat/?room={existing_room.pk}')
                    else:
                        # Create new DM room
                        room = ChatRoom.objects.create(
                            room_type='DIRECT',
                            name=f'{user.get_full_name()} & {other_user.get_full_name()}',
                            created_by=user
                        )
                        room.participants.add(user, other_user)

                        return redirect(f'/chat/?room={room.pk}')
                else:
                    messages.error(request, 'Please select a user.')

            except Exception as e:
                messages.error(request, f'Error creating conversation: {str(e)}')

        context = {
            'dm_list': dm_list,
            'page_title': 'Direct Messages',
        }

    except Exception as e:
        messages.error(request, f'Error loading messages: {str(e)}')
        context = {
            'dm_list': [],
            'page_title': 'Direct Messages',
        }

    return render(request, 'chat/direct_messages.html', context)


@login_required
def user_contacts(request):
    """
    View all users to start conversations.

    Shows:
    - All active users
    - Search functionality
    - Start chat button
    """
    try:
        # Get all active users except current user
        users = User.objects.filter(
            is_active=True
        ).exclude(pk=request.user.pk).order_by('first_name', 'last_name')

        # Search
        search_query = request.GET.get('q')
        if search_query:
            users = users.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query)
            )

        # Get existing DMs with each user
        user_rooms = {}
        for user in users:
            room = ChatRoom.objects.filter(
                room_type='DIRECT',
                participants=request.user
            ).filter(participants=user).first()

            if room:
                user_rooms[user.pk] = room.pk

        context = {
            'users': users,
            'user_rooms': user_rooms,
            'search_query': search_query,
            'page_title': 'Contacts',
        }

    except Exception as e:
        messages.error(request, f'Error loading contacts: {str(e)}')
        context = {
            'users': [],
            'user_rooms': {},
            'page_title': 'Contacts',
        }

    return render(request, 'chat/user_contacts.html', context)

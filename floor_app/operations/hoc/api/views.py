"""HOC API Views"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from floor_app.operations.hoc.models import HazardCategory, HazardObservation, HOCPhoto
from floor_app.operations.hoc.services import HOCService
from .serializers import (
    HazardCategorySerializer, HazardObservationSerializer, HazardObservationCreateSerializer,
    HOCAssignSerializer, HOCStatusUpdateSerializer, HOCCorrectiveActionSerializer,
    HOCVerifySerializer, HOCCloseSerializer, HOCPhotoSerializer, HOCPhotoUploadSerializer,
    HOCCommentSerializer, HOCCommentCreateSerializer, HOCStatusHistorySerializer
)


class HazardCategoryViewSet(viewsets.ModelViewSet):
    queryset = HazardCategory.objects.filter(is_active=True)
    serializer_class = HazardCategorySerializer
    permission_classes = [IsAuthenticated]


class HazardObservationViewSet(viewsets.ModelViewSet):
    serializer_class = HazardObservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = HazardObservation.objects.select_related(
            'category', 'submitted_by', 'assigned_to'
        ).prefetch_related('photos', 'comments')

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)

        # Filter by assigned user
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)

        # My observations
        if self.request.query_params.get('mine') == 'true':
            queryset = queryset.filter(submitted_by=self.request.user)

        return queryset

    def create(self, request):
        serializer = HazardObservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        observation = HOCService.create_observation(
            submitted_by=request.user,
            data=serializer.validated_data
        )

        return Response(
            HazardObservationSerializer(observation).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        serializer = HOCAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        assigned_to = User.objects.get(id=serializer.validated_data['assigned_to_id'])

        observation = HOCService.assign_observation(
            observation_id=int(pk),
            assigned_by=request.user,
            assigned_to=assigned_to,
            due_date=serializer.validated_data.get('due_date'),
            action_plan=serializer.validated_data.get('corrective_action_plan', '')
        )

        return Response(HazardObservationSerializer(observation).data)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        serializer = HOCStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        observation = HOCService.update_status(
            observation_id=int(pk),
            new_status=serializer.validated_data['status'],
            user=request.user,
            reason=serializer.validated_data.get('reason', '')
        )

        return Response(HazardObservationSerializer(observation).data)

    @action(detail=True, methods=['post'])
    def add_corrective_action(self, request, pk=None):
        serializer = HOCCorrectiveActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        observation = HOCService.add_corrective_action(
            observation_id=int(pk),
            user=request.user,
            action_taken=serializer.validated_data['corrective_action_taken']
        )

        return Response(HazardObservationSerializer(observation).data)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        serializer = HOCVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        observation = HOCService.verify_observation(
            observation_id=int(pk),
            verified_by=request.user,
            is_verified=serializer.validated_data['is_verified'],
            comments=serializer.validated_data.get('verification_comments', '')
        )

        return Response(HazardObservationSerializer(observation).data)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        serializer = HOCCloseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        observation = HOCService.close_observation(
            observation_id=int(pk),
            closed_by=request.user,
            closure_comments=serializer.validated_data.get('closure_comments', ''),
            actual_cost=serializer.validated_data.get('actual_cost')
        )

        return Response(HazardObservationSerializer(observation).data)

    @action(detail=True, methods=['post'])
    def add_photo(self, request, pk=None):
        serializer = HOCPhotoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        photo = HOCService.add_photo(
            observation_id=int(pk),
            photo_file=serializer.validated_data['photo'],
            photo_type=serializer.validated_data['photo_type'],
            caption=serializer.validated_data.get('caption', ''),
            uploaded_by=request.user
        )

        return Response(HOCPhotoSerializer(photo).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        serializer = HOCCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = HOCService.add_comment(
            observation_id=int(pk),
            comment_text=serializer.validated_data['comment'],
            commented_by=request.user,
            is_internal=serializer.validated_data.get('is_internal', False)
        )

        return Response(HOCCommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        observations = HOCService.get_overdue_observations()
        return Response(HazardObservationSerializer(observations, many=True).data)

    @action(detail=False, methods=['get'])
    def due_soon(self, request):
        days = int(request.query_params.get('days', 7))
        observations = HOCService.get_observations_due_soon(days=days)
        return Response(HazardObservationSerializer(observations, many=True).data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        from datetime import datetime
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        stats = HOCService.get_statistics(start_date, end_date)
        return Response(stats)

    @action(detail=False, methods=['get'])
    def my_statistics(self, request):
        stats = HOCService.get_user_statistics(request.user)
        return Response(stats)

    @action(detail=False, methods=['get'])
    def search(self, request):
        query_text = request.query_params.get('q', '')
        filters = {
            'status': request.query_params.get('status'),
            'severity': request.query_params.get('severity'),
            'category': request.query_params.get('category'),
        }
        filters = {k: v for k, v in filters.items() if v}

        observations = HOCService.search_observations(query_text, filters)
        return Response(HazardObservationSerializer(observations, many=True).data)

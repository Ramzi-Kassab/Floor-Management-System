"""Journey Management API Views"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from floor_app.operations.journey_management.models import JourneyPlan
from floor_app.operations.journey_management.services import JourneyService
from .serializers import (
    JourneyPlanSerializer, JourneyCreateSerializer, JourneyApproveSerializer,
    JourneyRejectSerializer, JourneyCompleteSerializer, JourneyCancelSerializer,
    WaypointCreateSerializer, JourneyWaypointSerializer, CheckInCreateSerializer,
    JourneyCheckInSerializer
)


class JourneyPlanViewSet(viewsets.ModelViewSet):
    serializer_class = JourneyPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = JourneyPlan.objects.select_related('traveler', 'approved_by').prefetch_related('waypoints', 'check_ins')

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # My journeys
        if self.request.query_params.get('mine') == 'true':
            queryset = queryset.filter(traveler=self.request.user)

        return queryset

    def create(self, request):
        serializer = JourneyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        journey = JourneyService.create_journey(
            traveler=request.user,
            data=serializer.validated_data
        )

        return Response(JourneyPlanSerializer(journey).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        journey = JourneyService.submit_for_approval(int(pk), request.user)
        return Response(JourneyPlanSerializer(journey).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        serializer = JourneyApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        journey = JourneyService.approve_journey(
            int(pk),
            request.user,
            serializer.validated_data.get('comments', '')
        )

        return Response(JourneyPlanSerializer(journey).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        serializer = JourneyRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        journey = JourneyService.reject_journey(
            int(pk),
            request.user,
            serializer.validated_data['reason']
        )

        return Response(JourneyPlanSerializer(journey).data)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        journey = JourneyService.start_journey(int(pk), request.user)
        return Response(JourneyPlanSerializer(journey).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        serializer = JourneyCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        journey = JourneyService.complete_journey(
            int(pk),
            request.user,
            **serializer.validated_data
        )

        return Response(JourneyPlanSerializer(journey).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        serializer = JourneyCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        journey = JourneyService.cancel_journey(
            int(pk),
            request.user,
            serializer.validated_data['reason']
        )

        return Response(JourneyPlanSerializer(journey).data)

    @action(detail=True, methods=['post'])
    def add_waypoint(self, request, pk=None):
        serializer = WaypointCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        waypoint = JourneyService.add_waypoint(int(pk), serializer.validated_data)

        return Response(JourneyWaypointSerializer(waypoint).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        serializer = CheckInCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        check_in = JourneyService.check_in(
            int(pk),
            serializer.validated_data['check_type'],
            serializer.validated_data['location_name'],
            serializer.validated_data
        )

        return Response(JourneyCheckInSerializer(check_in).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def active(self, request):
        journeys = JourneyService.get_active_journeys(request.user)
        return Response(JourneyPlanSerializer(journeys, many=True).data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        journeys = JourneyService.get_overdue_journeys()
        return Response(JourneyPlanSerializer(journeys, many=True).data)

    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        journeys = JourneyService.get_pending_approvals(request.user)
        return Response(JourneyPlanSerializer(journeys, many=True).data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        days = int(request.query_params.get('days', 7))
        journeys = JourneyService.get_upcoming_journeys(days, request.user)
        return Response(JourneyPlanSerializer(journeys, many=True).data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        from datetime import datetime
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        stats = JourneyService.get_statistics(start_date, end_date)
        return Response(stats)

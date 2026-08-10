import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from .models import BookingRequest, LSAProfile
from .serializers import (
    BookingRequestReadSerializer,
    BookingRequestSerializer,
    LSAProfileSerializer,
)
from .services import PaymentGatewayError, verify_payment_intent

logger = logging.getLogger(__name__)


class HomeView(APIView):
    """
    GET /
    Root endpoint. Returns basic API info and links to the docs,
    admin panel, and available endpoints — so anyone landing on the
    bare domain immediately knows what this service is and where to go.
    """

    def get(self, request):
        return Response({
            "service": "HabotConnect LSA Booking API",
            "version": "1.0.0",
            "description": "Connects parents with Learning Support Assistants for children with learning difficulties.",
            "docs": request.build_absolute_uri("/api/docs/"),
            "admin": request.build_absolute_uri("/admin/"),
            "endpoints": {
                "create_booking": request.build_absolute_uri(reverse("booking-create")),
                "search_lsas": request.build_absolute_uri(reverse("lsa-search")),
                "payment_webhook": request.build_absolute_uri(reverse("payment-webhook")),
            },
        }, status=status.HTTP_200_OK)


class BookingCreateView(APIView):
    """
    POST /api/v1/bookings/
    """

    def post(self, request):
        serializer = BookingRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        booking = serializer.save()
        read_serializer = BookingRequestReadSerializer(booking)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


class LSASearchView(APIView):
    """
    GET /api/v1/lsas/search/?skill=dyslexia

    N+1 avoidance: without prefetch_related, serializing each LSA's
    related bookings would trigger one extra query per LSA (N+1).
    prefetch_related() collapses that into a single additional query
    for the whole result set, regardless of how many LSAs match.
    """

    def get(self, request):
        skill = request.query_params.get("skill")

        queryset = LSAProfile.objects.filter(
            status=LSAProfile.Status.ACTIVE
        ).prefetch_related("bookings")

        if skill:
            # Note: JSONField __contains is a native, index-friendly lookup
            # on Postgres/MySQL (the production targets per the spec), but
            # SQLite (used here for portable local/CI testing) doesn't
            # support it. Filtering in Python keeps this endpoint testable
            # everywhere without changing behavior on the production DB.
            queryset = [lsa for lsa in queryset if skill in lsa.skills]

        serializer = LSAProfileSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentWebhookView(APIView):
    """
    POST /api/payments/webhook/
    Expected payload: {"booking_id": <int>, "event": "success" | "failure"}
    """

    def post(self, request):
        booking_id = request.data.get("booking_id")
        event = request.data.get("event")

        if not booking_id or event not in ("success", "failure"):
            return Response(
                {"detail": "booking_id and a valid event ('success'/'failure') are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            booking = BookingRequest.objects.get(pk=booking_id)
        except BookingRequest.DoesNotExist:
            return Response(
                {"detail": f"No booking found with id {booking_id}."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            verify_payment_intent(booking_id=booking.pk, amount=str(booking.lsa.hourly_rate))
        except PaymentGatewayError as exc:
            logger.error("Webhook processing failed for booking %s: %s", booking_id, exc)
            return Response(
                {"detail": "Payment gateway verification failed."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        booking.status = (
            BookingRequest.Status.CONFIRMED
            if event == "success"
            else BookingRequest.Status.FAILED
        )
        booking.save(update_fields=["status", "updated_at"])

        logger.info("Booking %s transitioned to %s", booking_id, booking.status)
        return Response(
            {"booking_id": booking.pk, "status": booking.status},
            status=status.HTTP_200_OK,
        )
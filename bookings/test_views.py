from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.models import BookingRequest, LSAProfile, Parent


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def parent(db):
    return Parent.objects.create(
        full_name="Anita Kumar",
        email="anita@example.com",
        phone_number="+919876543210",
        child_name="Rohan Kumar",
        child_learning_needs="Dyslexia support needed for reading comprehension.",
    )


@pytest.fixture
def lsa(db):
    return LSAProfile.objects.create(
        full_name="Priya Shah",
        email="priya@example.com",
        skills=["dyslexia", "adhd"],
        hourly_rate="500.00",
        status=LSAProfile.Status.ACTIVE,
    )


@pytest.mark.django_db
class TestBookingCreate:
    def test_create_booking_success(self, api_client, parent, lsa):
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=1)

        response = api_client.post(
            reverse("booking-create"),
            {
                "parent_id": parent.id,
                "lsa_id": lsa.id,
                "session_start": start.isoformat(),
                "session_end": end.isoformat(),
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.data["status"] == BookingRequest.Status.PENDING
        assert BookingRequest.objects.count() == 1

    def test_create_booking_rejects_overlap(self, api_client, parent, lsa):
        start = timezone.now() + timedelta(days=2)
        end = start + timedelta(hours=1)

        BookingRequest.objects.create(
            parent=parent, lsa=lsa, session_start=start, session_end=end
        )

        overlap_start = start + timedelta(minutes=30)
        overlap_end = overlap_start + timedelta(hours=1)

        response = api_client.post(
            reverse("booking-create"),
            {
                "parent_id": parent.id,
                "lsa_id": lsa.id,
                "session_start": overlap_start.isoformat(),
                "session_end": overlap_end.isoformat(),
            },
            format="json",
        )

        assert response.status_code == 400
        assert BookingRequest.objects.count() == 1

    def test_create_booking_rejects_end_before_start(self, api_client, parent, lsa):
        start = timezone.now() + timedelta(days=3)
        end = start - timedelta(hours=1)

        response = api_client.post(
            reverse("booking-create"),
            {
                "parent_id": parent.id,
                "lsa_id": lsa.id,
                "session_start": start.isoformat(),
                "session_end": end.isoformat(),
            },
            format="json",
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestLSASearch:
    def test_search_filters_by_skill(self, api_client, lsa):
        LSAProfile.objects.create(
            full_name="Other LSA",
            email="other@example.com",
            skills=["autism_support"],
            hourly_rate="450.00",
        )

        response = api_client.get(reverse("lsa-search"), {"skill": "dyslexia"})

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["full_name"] == "Priya Shah"

    def test_search_excludes_inactive_lsas(self, api_client, lsa):
        lsa.status = LSAProfile.Status.INACTIVE
        lsa.save()

        response = api_client.get(reverse("lsa-search"), {"skill": "dyslexia"})

        assert response.status_code == 200
        assert len(response.data) == 0


@pytest.mark.django_db
class TestPaymentWebhook:
    def test_webhook_confirms_booking_on_success(self, api_client, parent, lsa, mocker):
        booking = BookingRequest.objects.create(
            parent=parent,
            lsa=lsa,
            session_start=timezone.now() + timedelta(days=1),
            session_end=timezone.now() + timedelta(days=1, hours=1),
        )
        mocker.patch(
            "bookings.views.verify_payment_intent",
            return_value={"ok": True},
        )

        response = api_client.post(
            reverse("payment-webhook"),
            {"booking_id": booking.id, "event": "success"},
            format="json",
        )

        booking.refresh_from_db()
        assert response.status_code == 200
        assert booking.status == BookingRequest.Status.CONFIRMED

    def test_webhook_fails_booking_on_failure_event(self, api_client, parent, lsa, mocker):
        booking = BookingRequest.objects.create(
            parent=parent,
            lsa=lsa,
            session_start=timezone.now() + timedelta(days=1),
            session_end=timezone.now() + timedelta(days=1, hours=1),
        )
        mocker.patch(
            "bookings.views.verify_payment_intent",
            return_value={"ok": True},
        )

        response = api_client.post(
            reverse("payment-webhook"),
            {"booking_id": booking.id, "event": "failure"},
            format="json",
        )

        booking.refresh_from_db()
        assert response.status_code == 200
        assert booking.status == BookingRequest.Status.FAILED

    def test_webhook_returns_404_for_unknown_booking(self, api_client):
        response = api_client.post(
            reverse("payment-webhook"),
            {"booking_id": 9999, "event": "success"},
            format="json",
        )
        assert response.status_code == 404


@pytest.mark.django_db
def test_home_endpoint_returns_api_info(api_client):
    response = api_client.get("/")
    assert response.status_code == 200
    assert response.data["service"] == "HabotConnect LSA Booking API"
    assert "docs" in response.data
    assert "endpoints" in response.data
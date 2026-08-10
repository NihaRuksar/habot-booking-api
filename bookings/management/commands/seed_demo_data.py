from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from bookings.models import BookingRequest, LSAProfile, Parent


class Command(BaseCommand):
    help = "Seeds the database with realistic demo data for presentation/testing."

    def handle(self, *args, **options):
        Parent.objects.all().delete()
        LSAProfile.objects.all().delete()
        BookingRequest.objects.all().delete()

        parent1 = Parent.objects.create(
            full_name="Anita Kumar",
            email="anita.kumar@example.com",
            phone_number="+919876543210",
            child_name="Rohan Kumar",
            child_learning_needs="Dyslexia support for reading comprehension.",
        )
        parent2 = Parent.objects.create(
            full_name="Farah Sheikh",
            email="farah.sheikh@example.com",
            phone_number="+919123456780",
            child_name="Zayn Sheikh",
            child_learning_needs="ADHD support, needs structured attention routines.",
        )

        lsa1 = LSAProfile.objects.create(
            full_name="Priya Shah",
            email="priya.shah@example.com",
            skills=["dyslexia", "reading_support"],
            hourly_rate="500.00",
            status=LSAProfile.Status.ACTIVE,
        )
        lsa2 = LSAProfile.objects.create(
            full_name="Karan Mehta",
            email="karan.mehta@example.com",
            skills=["adhd", "autism_support"],
            hourly_rate="600.00",
            status=LSAProfile.Status.ACTIVE,
        )
        LSAProfile.objects.create(
            full_name="Neha Verma",
            email="neha.verma@example.com",
            skills=["dyslexia", "adhd"],
            hourly_rate="550.00",
            status=LSAProfile.Status.ON_LEAVE,
        )

        start = timezone.now() + timedelta(days=1)
        BookingRequest.objects.create(
            parent=parent1,
            lsa=lsa1,
            session_start=start,
            session_end=start + timedelta(hours=1),
            status=BookingRequest.Status.CONFIRMED,
        )
        BookingRequest.objects.create(
            parent=parent2,
            lsa=lsa2,
            session_start=start + timedelta(days=1),
            session_end=start + timedelta(days=1, hours=1),
            status=BookingRequest.Status.PENDING,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded 2 parents, 3 LSAs, and 2 bookings successfully."
            )
        )
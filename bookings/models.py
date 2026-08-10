from django.core.validators import RegexValidator
from django.db import models
from django.core.exceptions import ValidationError

# E.164 international format: optional +, then 7 to 15 digits total.
# Examples: +919876543210 (India), +14155552671 (US), +447911123456 (UK)
phone_regex = RegexValidator(
    regex=r'^\+?[1-9]\d{6,14}$',
    message="Phone number must be entered in international format: '+919876543210'."
)


class Parent(models.Model):
    """A parent looking for a Learning Support Assistant for their child."""
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(max_length=17, validators=[phone_regex])
    child_name = models.CharField(max_length=150)
    child_learning_needs = models.TextField(
        help_text="Free-text description of the child's learning difficulty/needs"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"{self.full_name} (parent of {self.child_name})"


class LSAProfile(models.Model):
    """A Learning Support Assistant available for booking."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        ON_LEAVE = "ON_LEAVE", "On Leave"

    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True, db_index=True)
    # Queryable skill tags, e.g. ["dyslexia", "adhd", "autism_support"]
    skills = models.JSONField(default=list, blank=True)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.status})"


class BookingRequest(models.Model):
    """A booking session request linking a Parent to an LSA for a time slot."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Payment"
        CONFIRMED = "CONFIRMED", "Confirmed"
        FAILED = "FAILED", "Payment Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    parent = models.ForeignKey(
        Parent, on_delete=models.CASCADE, related_name="bookings"
    )
    lsa = models.ForeignKey(
        LSAProfile, on_delete=models.CASCADE, related_name="bookings"
    )
    session_start = models.DateTimeField(db_index=True)
    session_end = models.DateTimeField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            # Speeds up the overlap-check query (filtering by lsa + time range)
            models.Index(fields=["lsa", "session_start", "session_end"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(session_end__gt=models.F("session_start")),
                name="session_end_after_start",
            ),
        ]

    def clean(self):
        """
        Application-level double-booking guard (in addition to the check
        constraint above, which only guarantees end > start).
        Overlap rule: new.start < existing.end AND new.end > existing.start
        """
        overlapping = BookingRequest.objects.filter(
            lsa=self.lsa,
            status__in=[self.Status.PENDING, self.Status.CONFIRMED],
        ).exclude(pk=self.pk).filter(
            session_start__lt=self.session_end,
            session_end__gt=self.session_start,
        )
        if overlapping.exists():
            raise ValidationError(
                "This LSA already has a booking that overlaps with the requested time slot."
            )

    def __str__(self):
        return f"Booking #{self.pk}: {self.parent} -> {self.lsa} ({self.status})"
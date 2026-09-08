from django.db import models
import uuid


class Plan(models.Model):
    BILLING_INTERVAL_CHOICES = (
        ("month", "Monthly"),
        ("year", "Yearly"),
    )
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=100
    )
    code = models.CharField(
        max_length=50,
        unique=True
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    billing_interval = models.CharField(
        max_length=20,
        choices=BILLING_INTERVAL_CHOICES
    )
    billing_interval_count = models.PositiveIntegerField(
        default=1
    )
    description = models.TextField(
        blank=True,
        null=True
    )
    is_recommended = models.BooleanField(
        default=False
    )
    is_active = models.BooleanField(
        default=True
    )
    razorpay_plan_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    def __str__(self):
        return f"{self.name} - ₹{self.price}"
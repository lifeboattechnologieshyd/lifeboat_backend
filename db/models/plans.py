from django.db import models
import uuid

from db.models import AuditModel, UserMaster


class Plan(AuditModel):
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

    class Meta:
        db_table = "plans"


class Subscription(AuditModel):

    STATUS_CHOICES = (
        ("created", "Created"),
        ("active", "Active"),
        ("paused", "Paused"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
        ("failed", "Failed"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.ForeignKey(
        UserMaster,
        on_delete=models.PROTECT,
        related_name="subscriptions"
    )

    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions"
    )

    razorpay_subscription_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="created"
    )

    start_at = models.DateTimeField(
        null=True,
        blank=True
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True
    )
    next_charge_at = models.DateTimeField(
        null=True,
        blank=True
    )

    end_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    def __str__(self):
        return f"{self.user} - ₹{self.plan} - {self.created_at}"

    class Meta:
        db_table = "subscriptions"


class PaymentTransaction(AuditModel):

    STATUS_CHOICES = (
        ("created", "Created"),
        ("authorized", "Authorized"),
        ("captured", "Captured"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.ForeignKey(
        UserMaster,
        on_delete=models.PROTECT,
        related_name="payments"
    )

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True
    )

    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="payments"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=10,
        default="INR"
    )

    razorpay_payment_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )
    razorpay_subscription_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    razorpay_order_id = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    razorpay_signature = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="created"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "transactions"
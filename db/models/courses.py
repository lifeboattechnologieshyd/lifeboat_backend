import uuid
from django.db import models
from db.models import AuditModel


class Category(AuditModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=100,
        unique=True
    )
    icon = models.CharField(
        max_length=100,
        unique=True
    )
    description = models.TextField(
        blank=True,
        null=True
    )
    is_active = models.BooleanField(
        default=True
    )
    sort_order = models.PositiveIntegerField(
        default=0
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "category"
        ordering = ["sort_order", "name"]


class Technology(AuditModel):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(
        max_length=100,
        unique=True
    )
    description = models.TextField(
        blank=True,
        null=True
    )
    categories = models.ManyToManyField(
        Category,
        related_name="technologies",
        blank=True
    )
    is_active = models.BooleanField(
        default=True
    )
    sort_order = models.PositiveIntegerField(
        default=0
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    def __str__(self):
        return self.name

    class Meta:
        db_table = "technology"
        ordering = ["sort_order", "name"]

class Course(AuditModel):

    LEVEL_CHOICES = (
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    )
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    title = models.CharField(
        max_length=200
    )
    description = models.TextField(
        blank=True,
        null=True
    )
    thumbnail = models.URLField(
        blank=True,
        null=True
    )
    categories = models.ManyToManyField(
        Category,
        related_name="courses",
        blank=True
    )
    technologies = models.ManyToManyField(
        Technology,
        related_name="courses",
        blank=True
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default="beginner"
    )
    duration = models.PositiveIntegerField(
        default=0,
        help_text="Total course duration in minutes"
    )
    total_lessons = models.PositiveIntegerField(
        default=0
    )
    is_published = models.BooleanField(
        default=False
    )
    sort_order = models.PositiveIntegerField(
        default=0
    )
    def __str__(self):
        return self.title

    class Meta:
        db_table = "course"
        ordering = ["sort_order", "-created_at"]


class CourseModule(AuditModel):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="modules"
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    sort_order = models.PositiveIntegerField(
        default=0
    )

    is_published = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.title

    class Meta:
        db_table = "course_module"
        ordering = ["sort_order", "created_at"]

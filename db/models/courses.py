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

class Lesson(AuditModel):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    module = models.ForeignKey(
        CourseModule,
        on_delete=models.PROTECT,
        related_name="lessons"
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    video = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )
    thumbnail = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    duration = models.PositiveIntegerField(
        default=0,
        help_text="Lesson duration in seconds"
    )

    sort_order = models.PositiveIntegerField(
        default=0
    )

    is_preview = models.BooleanField(
        default=False
    )
    is_published = models.BooleanField(
        default=False
    )
    def __str__(self):
        return self.title
    class Meta:
        db_table = "lesson"
        ordering = ["sort_order", "created_at"]


class Video(AuditModel):
    STATUS_CHOICES = (
        ("uploaded", "Uploaded"),
        ("processing", "Processing"),
        ("ready", "Ready"),
        ("failed", "Failed"),
    )
    LANGUAGE_CHOICES = (
        ("english", "English"),
        ("telugu", "Telugu"),
        ("hindi", "Hindi"),
    )
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=200)

    language = models.CharField(
        max_length=30,
        choices=LANGUAGE_CHOICES,
        default="english"
    )
    original_key = models.CharField(
        max_length=500,
        help_text="S3 key of the original uploaded video"
    )

    hls_key = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="S3 key of the HLS master playlist"
    )
    media_job_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="uploaded"
    )
    duration = models.PositiveIntegerField(
        default=0,
        help_text="Video duration in seconds"
    )
    file_size = models.PositiveBigIntegerField(
        default=0,
        help_text="Original video size in bytes"
    )
    error_message = models.TextField(
        blank=True,
        null=True
    )
    def __str__(self):
        return self.name

    class Meta:
        db_table = "video"
        ordering = ["-created_at"]
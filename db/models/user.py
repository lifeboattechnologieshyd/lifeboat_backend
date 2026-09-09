import uuid

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models

from db.models import AuditModel


class CustomUserManager(BaseUserManager):
    def create_user(self, mobile, password=None, **extra_fields):
        if not mobile:
            raise ValueError("The Mobile Number must be set")
        user = self.model(mobile=mobile, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user


class UserMaster(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=30)
    mobile = models.CharField(max_length=20, null=True)
    email = models.EmailField(max_length=100, unique=True, null=True)
    image = models.CharField(max_length=255, null=True)
    is_active = models.BooleanField(default=True)
    updated_by = models.CharField(max_length=255,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    bio = models.TextField(blank=True,null=True)
    objects = CustomUserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return str(self.email)

    class Meta:
        db_table = "user-master"


class MagicLoginToken(AuditModel):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    email = models.EmailField(max_length=100)
    token_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "email-token"


class OTP(AuditModel):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    email = models.EmailField(max_length=100)
    otp = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True,blank=True)
    attempts = models.PositiveIntegerField(default=0)
    class Meta:
        db_table = "email-otp"


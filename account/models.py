from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from common.models import Role, BaseModel
from account.manager import UserManager

class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(unique=True)
    google_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=150, blank=True)
    avatar_url = models.URLField(blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    region = models.CharField(max_length=100, blank=True)
    target_major = models.CharField(max_length=150, blank=True)
    xp_total = models.PositiveIntegerField(default=0)
    consent_share_with_universities = models.BooleanField(default=False)
    consent_updated_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if self.google_id == "":
            self.google_id = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
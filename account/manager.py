from django.contrib.auth.base_user import BaseUserManager

from common.models import Role


class UserManager(BaseUserManager):
    def create_user(self, email, **extra_fields):
        if not email:
            raise ValueError("Email kiritilishi shart")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_unusable_password()   # faqat Google orqali kiradi, parol umuman yo'q
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.ADMIN)
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)   # faqat Django admin panelga kirish uchun
        user.save(using=self._db)
        return user

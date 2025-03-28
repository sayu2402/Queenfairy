from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db import models
from django.utils import timezone
import random
import string

class UserManager(BaseUserManager):
    def create_user(self, email=None, phone=None, first_name="", last_name="", password=None, **extra_fields):
        if not email and not phone:
            raise ValueError("Either email or phone must be provided.")
        
        email = self.normalize_email(email) if email else None
        user = self.model(email=email, phone=phone, first_name=first_name, last_name=last_name, **extra_fields)
        
        if password:  # Allow password in the future
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    password = models.CharField(max_length=128, blank=True, null=True)  # For future password support

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)  # Admin user flag

    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)

    USERNAME_FIELD = "email"  # Email-based authentication
    REQUIRED_FIELDS = []  # No mandatory fields since email/phone is dynamic

    objects = UserManager()

    def __str__(self):
        return self.email if self.email else self.phone


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)

    @staticmethod
    def generate_otp():
        return ''.join(random.choices(string.digits, k=6))

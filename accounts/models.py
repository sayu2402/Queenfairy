from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone

# Create your models here.


# Custom Manager for User model
class UserManager(BaseUserManager):
    def create_user(self, email_or_phone, password=None, **extra_fields):
        if not email_or_phone:
            raise ValueError("The Email/Phone number must be set")
        user = self.model(email_or_phone=email_or_phone, **extra_fields)
        user.set_password(password)  # Encrypt password
        user.save(using=self._db)
        return user

    def create_superuser(self, email_or_phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email_or_phone, password, **extra_fields)

# User model
class User(AbstractBaseUser):
    EMAIL = 'email'
    PHONE = 'phone'
    CHOICE = [
        (EMAIL, 'Email'),
        (PHONE, 'Phone'),
    ]
    
    email_or_phone = models.CharField(max_length=255, unique=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    verification_choice = models.CharField(max_length=5, choices=CHOICE, default=EMAIL)
    
    # For password management (for future use)
    password = models.CharField(max_length=255)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    objects = UserManager()

    USERNAME_FIELD = 'email_or_phone'
    REQUIRED_FIELDS = ['verification_choice']
    
    def __str__(self):
        return self.email_or_phone

    def is_verified(self):
        if self.verification_choice == self.EMAIL and self.email_verified:
            return True
        elif self.verification_choice == self.PHONE and self.phone_verified:
            return True
        return False


# OTP Model
class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_set')
    otp_code = models.CharField(max_length=6)
    expiry_time = models.DateTimeField()

    def __str__(self):
        return f"OTP {self.otp_code} for {self.user.email_or_phone}"

    def is_expired(self):
        return timezone.now() > self.expiry_time

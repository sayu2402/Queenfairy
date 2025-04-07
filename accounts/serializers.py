from rest_framework import serializers
from .models import User, OTP
from datetime import timedelta
from django.utils import timezone


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]

    def validate(self, attrs):
        email = attrs.get("email")
        phone = attrs.get("phone")

        if not email and not phone:
            raise serializers.ValidationError("Either email or phone must be provided.")

        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email is already registered.")

        if phone and User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("Phone number is already registered.")

        return attrs


class OTPVerifySerializer(serializers.Serializer):
    username = serializers.CharField()
    otp = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get("username")
        otp_code = attrs.get("otp")

        otp_record = OTP.objects.filter(
            otp=otp_code,
            username=username,
            created_at__gte=timezone.now() - timedelta(minutes=5),
        ).first()

        if not otp_record:
            raise serializers.ValidationError("Invalid or expired OTP.")

        return attrs

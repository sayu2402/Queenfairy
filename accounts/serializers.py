from rest_framework import serializers
from .models import User, OTP
import random
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


class GenerateOTPSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()
    verification_choice = serializers.ChoiceField(choices=User.CHOICE)

    def validate(self, data):
        email_or_phone = data['email_or_phone']
        verification_choice = data['verification_choice']

        # Check email validation
        if verification_choice == User.EMAIL and '@' not in email_or_phone:
            raise serializers.ValidationError("Please provide a valid email address.")

        # Check phone validation
        if verification_choice == User.PHONE and not email_or_phone.isdigit():
            raise serializers.ValidationError("Please provide a valid phone number.")

        return data

    def create(self, validated_data):
        email_or_phone = validated_data['email_or_phone']
        verification_choice = validated_data['verification_choice']

        # Get or create the user
        user, created = User.objects.get_or_create(email_or_phone=email_or_phone)
        user.verification_choice = verification_choice
        user.save()

        # Delete old OTP if exists
        OTP.objects.filter(user=user).delete()

        # Generate OTP
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        expiry_time = timezone.now() + timezone.timedelta(minutes=5)

        otp_instance = OTP.objects.create(user=user, otp_code=otp_code, expiry_time=expiry_time)

        # Send OTP via email or phone
        if verification_choice == User.EMAIL:
            send_mail(
                'Your OTP Code',
                f'Your OTP code is {otp_code}',
                settings.EMAIL_HOST_USER,
                [email_or_phone],
                fail_silently=False,
            )
        elif verification_choice == User.PHONE:
            # Integrate with SMS service here
            pass

        return otp_instance


class VerifyOTPSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()
    otp_code = serializers.CharField(max_length=6)

    def validate(self, data):
        email_or_phone = data['email_or_phone']
        otp_code = data['otp_code']

        user = User.objects.filter(email_or_phone=email_or_phone).first()
        if not user:
            raise serializers.ValidationError("User not found.")

        otp_instance = OTP.objects.filter(user=user, otp_code=otp_code).last()
        if not otp_instance:
            raise serializers.ValidationError("Invalid OTP.")

        if otp_instance.expiry_time < timezone.now():
            raise serializers.ValidationError("OTP has expired.")

        return data

    def save(self):
        email_or_phone = self.validated_data['email_or_phone']
        user = User.objects.get(email_or_phone=email_or_phone)

        if user.verification_choice == User.EMAIL:
            user.email_verified = True
        else:
            user.phone_verified = True
        
        user.save()

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }



from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    email_or_phone = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    
    class Meta:
        model = User
        fields = ['email_or_phone', 'first_name', 'last_name']

    def validate_email_or_phone(self, value):
        if '@' in value:
            if User.objects.filter(email_or_phone=value).exists():
                raise serializers.ValidationError("This email is already registered.")
        elif value.isdigit() and len(value) == 10:
            if User.objects.filter(email_or_phone=value).exists():
                raise serializers.ValidationError("This phone number is already registered.")
        else:
            raise serializers.ValidationError("Invalid email or phone number format.")
        return value
    
    def validate(self, data):
        email_or_phone = data.get('email_or_phone')
        user = User.objects.filter(email_or_phone=email_or_phone).first()
        
        if not user:
            raise serializers.ValidationError("OTP verification required before registration.")
        
        if user.verification_choice == User.EMAIL and not user.email_verified:
            raise serializers.ValidationError("OTP not verified for email.")
        
        if user.verification_choice == User.PHONE and not user.phone_verified:
            raise serializers.ValidationError("OTP not verified for phone.")
        
        return data

    def create(self, validated_data):
        user = User.objects.get(email_or_phone=validated_data['email_or_phone'])
        user.first_name = validated_data['first_name']
        user.last_name = validated_data['last_name']
        user.save()
        return user

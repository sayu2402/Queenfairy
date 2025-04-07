from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import random
import string
import requests
from django.conf import settings
from django.core.mail import send_mail
from .models import User, OTP
from .serializers import RegisterSerializer, OTPVerifySerializer


class GenerateOTPView(APIView):
    def post(self, request):
        username = request.data.get("username")  # Can be email or phone

        if not username:
            return Response(
                {"error": "Email or phone number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the username is an email or phone number
        if "@" in username:
            if User.objects.filter(email=username).exists():
                return Response(
                    {"error": "Email is already registered."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            if User.objects.filter(phone=username).exists():
                return Response(
                    {"error": "Phone number is already registered."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Generate OTP
        otp_code = "".join(random.choices(string.digits, k=6))

        # Save OTP in the database
        OTP.objects.create(user=None, otp=otp_code, username=username)

        # Send OTP via Email or SMS
        if "@" in username:
            # Send OTP via SMTP Email
            send_mail(
                "Your OTP Code",
                f"Your OTP code is {otp_code}. It expires in 5 minutes.",
                settings.DEFAULT_FROM_EMAIL,
                [username],
                fail_silently=False,
            )
        else:
            # Send OTP via Fast2SMS
            api_key = "FAST2SMS_API_KEY"
            url = f"https://www.fast2sms.com/dev/bulkV2?authorization={api_key}&route=v3&message=Your OTP code is {otp_code}. It expires in 5 minutes.&language=english&flash=0&numbers={username}"
            requests.get(url)

        return Response(
            {"message": "OTP sent successfully. Proceed with verification."},
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)

        if serializer.is_valid():
            username = serializer.validated_data["username"]

            # Store verified username in session
            request.session["verified_username"] = username

            return Response(
                {"message": "OTP verified. Proceed with registration."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterUserView(APIView):
    def post(self, request):
        verified_username = request.session.get("verified_username")

        if not verified_username:
            return Response(
                {"error": "OTP verification required before registration."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Use the serializer to handle registration
        data = {
            "first_name": request.data.get("first_name"),
            "last_name": request.data.get("last_name"),
        }

        if "@" in verified_username:
            data["email"] = verified_username
            data["phone"] = request.data.get("phone")
        else:
            data["phone"] = verified_username
            data["email"] = request.data.get("email")

        # Validate and create user using the serializer
        serializer = RegisterSerializer(data=data)

        if serializer.is_valid():
            user = serializer.save()

            # Clear session after successful registration
            del request.session["verified_username"]

            return Response(
                {
                    "message": "Registration successful.",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "phone": user.phone,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

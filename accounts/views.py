import random
import string
import requests
from django.utils import timezone
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, OTP
from .serializers import RegisterSerializer
from datetime import timedelta
from django.core.mail import send_mail


class GenerateOTPView(APIView):
    def post(self, request):
        username = request.data.get("username")  # Can be email or phone

        if not username:
            return Response({"error": "Email or phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the username is an email or phone number
        if "@" in username:
            if User.objects.filter(email=username).exists():
                return Response({"error": "Email is already registered."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if User.objects.filter(phone=username).exists():
                return Response({"error": "Phone number is already registered."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate OTP
        otp_code = ''.join(random.choices(string.digits, k=6))

        # Save OTP in the database
        OTP.objects.create(
            user=None,
            otp=otp_code,
            username=username
        )

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

        return Response({"message": "OTP sent successfully. Proceed with verification."}, status=status.HTTP_200_OK)



class VerifyOTPView(APIView):
    def post(self, request):
        username = request.data.get("username")  # Can be email or phone
        otp_code = request.data.get("otp")

        if not username or not otp_code:
            return Response({"error": "Username and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Debugging: print out the username and otp_code for validation
        print(f"Received username: {username}, OTP: {otp_code}")

        # Check if OTP is valid (5-minute window check)
        otp_record = OTP.objects.filter(
            otp=otp_code,
            username=username,
            created_at__gte=timezone.now() - timedelta(minutes=5)
        ).first()

        # Debugging: Print out the OTP record if found
        if otp_record:
            print(f"Found OTP record: {otp_record.otp}, Created at: {otp_record.created_at}")
        else:
            print("No OTP record found or OTP is expired.")

        if not otp_record:
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        # Store verified email/phone in session
        request.session["verified_username"] = username

        return Response({"message": "OTP verified. Proceed with registration."}, status=status.HTTP_200_OK)




class RegisterUserView(APIView):
    def post(self, request):
        verified_username = request.session.get("verified_username")

        if not verified_username:
            return Response({"error": "OTP verification required before registration."}, status=status.HTTP_400_BAD_REQUEST)

        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        email = None
        phone = None

        if "@" in verified_username:
            email = verified_username  # Auto-fill email
            phone = request.data.get("phone")  # User must enter phone (optional)
        else:
            phone = verified_username  # Auto-fill phone
            email = request.data.get("email")  # User must enter email (optional)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email is already registered."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(phone=phone).exists():
            return Response({"error": "Phone number is already registered."}, status=status.HTTP_400_BAD_REQUEST)

        # Create user
        user = User.objects.create(
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name
        )

        # Clear session after successful registration
        del request.session["verified_username"]

        return Response({
            "message": "Registration successful.",
            "user": {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }, status=status.HTTP_201_CREATED)

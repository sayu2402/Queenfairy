from django.urls import path
from .views import GenerateOTPView, VerifyOTPView, RegisterView

urlpatterns = [
    path('generate-otp/', GenerateOTPView.as_view(), name='generate_otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('register/', RegisterView.as_view(), name='register_user'),
]

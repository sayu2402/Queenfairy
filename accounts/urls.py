from django.urls import path
from .views import GenerateOTPView, VerifyOTPView, RegisterUserView

urlpatterns = [
    path("generate-otp/", GenerateOTPView.as_view(), name="generate-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("register/", RegisterUserView.as_view(), name="register"),
]

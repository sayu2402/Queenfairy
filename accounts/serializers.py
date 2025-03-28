from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "phone", "first_name", "last_name"]

    def validate(self, data):
        if not data.get("email") and not data.get("phone"):
            raise serializers.ValidationError("Either email or phone number is required.")

        if not data.get("first_name") or not data.get("last_name"):
            raise serializers.ValidationError("First name and last name are required.")

        return data

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        return user

# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'gender',
                  'user_type', 'phone_number', 'specialization', 
                  'license_number', 'license_image_url', 'is_approved']
        read_only_fields = ['is_approved']
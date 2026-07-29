# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserRelationship

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    license_image_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'gender',
                  'user_type', 'phone_number', 'specialization', 
                  'license_number', 'license_image_url', 'is_approved']
        read_only_fields = ['is_approved']

    def validate_license_image_url(self, value):
        if value in [None, '']:
            return ''
        if not isinstance(value, str):
            raise serializers.ValidationError('يجب أن يكون نصاً')
        return value.strip()


class UserRelationshipSerializer(serializers.ModelSerializer):
    doctor = UserSerializer(read_only=True)
    patient = UserSerializer(read_only=True)

    class Meta:
        model = UserRelationship
        fields = ['id', 'doctor', 'patient', 'relationship_type', 'status',
                  'can_view_medications', 'can_receive_alerts', 'can_view_reports',
                  'can_make_medical_decisions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'doctor', 'patient', 'created_at', 'updated_at']
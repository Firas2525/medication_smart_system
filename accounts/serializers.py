# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

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
import time
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


def create_access_token(user):
    payload = {
        'user_id': user.pk,
        'type': 'access',
        'exp': (timezone.now() + timedelta(hours=6)).timestamp(),
    }
    return signing.dumps(payload)


def create_refresh_token(user):
    payload = {
        'user_id': user.pk,
        'type': 'refresh',
        'exp': (timezone.now() + timedelta(days=30)).timestamp(),
    }
    return signing.dumps(payload)


def decode_signed_token(token):
    payload = signing.loads(token)
    exp = payload.get('exp')
    if exp and time.time() > float(exp):
        raise ValueError('Token expired')
    return payload


class SignedTokenAuthentication(BaseAuthentication):
    """Simple bearer-token authentication based on Django signing."""

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ', 1)[1].strip()
        if not token:
            return None

        try:
            payload = decode_signed_token(token)
        except Exception as exc:
            raise AuthenticationFailed('Invalid or expired token') from exc

        if payload.get('type') != 'access':
            raise AuthenticationFailed('Invalid token type')

        user_id = payload.get('user_id')
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist as exc:
            raise AuthenticationFailed('User not found') from exc

        if not user.is_active:
            raise AuthenticationFailed('User is inactive')

        return user, token

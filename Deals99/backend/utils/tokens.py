"""Simple token helpers using Django signing for email verification and password reset tokens.
Tokens are time-limited and safe to include in URLs.
"""
from django.core import signing
from django.conf import settings

SALT = 'deals99.email'  # simple constant salt for signing


def make_email_verification_token(user):
    payload = {'user_id': user.pk, 'email': user.email}
    token = signing.dumps(payload, salt=SALT)
    return token


def verify_email_verification_token(token, max_age=60 * 60 * 24):
    try:
        data = signing.loads(token, salt=SALT, max_age=max_age)
        return data
    except signing.BadSignature:
        return None
    except signing.SignatureExpired:
        return None


# Password reset helpers (same signing mechanism, separate salt for safety)
PASSWORD_RESET_SALT = 'deals99.password.reset'


def make_password_reset_token(user):
    payload = {'user_id': user.pk, 'email': user.email}
    return signing.dumps(payload, salt=PASSWORD_RESET_SALT)


def verify_password_reset_token(token, max_age=60 * 60 * 24):
    try:
        data = signing.loads(token, salt=PASSWORD_RESET_SALT, max_age=max_age)
        return data
    except signing.BadSignature:
        return None
    except signing.SignatureExpired:
        return None

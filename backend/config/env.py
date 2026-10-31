"""Strict environment parsing for deployment settings."""
import os


def boolean_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in ('1', 'true', 'yes', 'on'):
        return True
    if normalized in ('0', 'false', 'no', 'off'):
        return False
    raise ValueError(f'{name} must be true or false (received an invalid value).')


def list_env(name: str, default: str = '') -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(',') if item.strip()]


def deployment_secret(debug: bool) -> str:
    secret = os.getenv('DJANGO_SECRET_KEY', '')
    if not debug and (len(secret) < 50 or secret == 'development-only-change-me'):
        raise ValueError('DJANGO_SECRET_KEY must be a unique secret of at least 50 characters when DJANGO_DEBUG=false.')
    return secret or 'development-only-change-me'

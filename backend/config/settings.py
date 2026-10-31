import os
from pathlib import Path
from .env import boolean_env, list_env, deployment_secret
BASE_DIR=Path(__file__).resolve().parent.parent
DEBUG=boolean_env('DJANGO_DEBUG', True)
SECRET_KEY=deployment_secret(DEBUG)
ALLOWED_HOSTS=list_env('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1' if DEBUG else '')
if not DEBUG and not ALLOWED_HOSTS:
    raise ValueError('DJANGO_ALLOWED_HOSTS must be configured when DJANGO_DEBUG=false.')
INSTALLED_APPS=['django.contrib.auth','django.contrib.contenttypes','rest_framework','corsheaders','routing']
MIDDLEWARE=['corsheaders.middleware.CorsMiddleware','django.middleware.common.CommonMiddleware']
ROOT_URLCONF='config.urls'
DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'db.sqlite3'}}
CORS_ALLOWED_ORIGINS=list_env('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174' if DEBUG else '')
SESSION_COOKIE_SECURE=not DEBUG
CSRF_COOKIE_SECURE=not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF=True
# Configure TLS termination / proxy forwarding explicitly in your hosting platform.
# Do not blindly trust X-Forwarded-Proto from untrusted clients.
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
USE_TZ=True
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

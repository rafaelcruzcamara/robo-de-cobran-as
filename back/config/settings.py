"""Configuração local mínima para persistência Django."""

import os
import secrets
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
DEBUG = os.environ.get("DJANGO_DEBUG", "false").casefold() == "true"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "Defina DJANGO_SECRET_KEY quando DEBUG estiver desativado."
        )
    SECRET_KEY = secrets.token_urlsafe(50)
hosts_configurados = os.environ.get("DJANGO_ALLOWED_HOSTS")
if hosts_configurados:
    ALLOWED_HOSTS = [
        host.strip() for host in hosts_configurados.split(",") if host.strip()
    ]
elif DEBUG:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
else:
    ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cobrancas.apps.CobrancasConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [PROJECT_DIR / "front" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
COBRANCAS_DB_ENGINE = os.environ.get("COBRANCAS_DB_ENGINE", "sqlite").casefold()
if COBRANCAS_DB_ENGINE in {"postgres", "postgresql"}:
    campos_db_obrigatorios = (
        "COBRANCAS_DB_NAME",
        "COBRANCAS_DB_USER",
        "COBRANCAS_DB_PASSWORD",
        "COBRANCAS_DB_HOST",
    )
    campos_db_ausentes = [
        campo for campo in campos_db_obrigatorios if not os.environ.get(campo)
    ]
    if campos_db_ausentes:
        raise ImproperlyConfigured(
            "Defina as variáveis PostgreSQL: " + ", ".join(campos_db_ausentes)
        )
    opcoes_postgres = {}
    sslmode = os.environ.get("COBRANCAS_DB_SSLMODE")
    if sslmode:
        opcoes_postgres["sslmode"] = sslmode
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["COBRANCAS_DB_NAME"],
            "USER": os.environ["COBRANCAS_DB_USER"],
            "PASSWORD": os.environ["COBRANCAS_DB_PASSWORD"],
            "HOST": os.environ["COBRANCAS_DB_HOST"],
            "PORT": os.environ.get("COBRANCAS_DB_PORT", "5432"),
            "CONN_MAX_AGE": int(os.environ.get("COBRANCAS_DB_CONN_MAX_AGE", "60")),
            "OPTIONS": opcoes_postgres,
        }
    }
elif COBRANCAS_DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get(
                "COBRANCAS_DB_PATH", str(PROJECT_DIR / "db.sqlite3")
            ),
        }
    }
else:
    raise ImproperlyConfigured("COBRANCAS_DB_ENGINE deve ser sqlite ou postgresql.")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "America/Sao_Paulo"
LANGUAGE_CODE = "pt-br"
FILE_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024
FILE_UPLOAD_HANDLERS = ["django.core.files.uploadhandler.MemoryFileUploadHandler"]
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        )
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [PROJECT_DIR / "front" / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = (
    os.environ.get(
        "DJANGO_SECURE_SSL_REDIRECT", "false" if DEBUG else "true"
    ).casefold()
    == "true"
)
if os.environ.get("DJANGO_TRUST_PROXY_SSL_HEADER", "false").casefold() == "true":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    os.environ.get("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", "false").casefold()
    == "true"
)
SECURE_HSTS_PRELOAD = (
    os.environ.get("DJANGO_SECURE_HSTS_PRELOAD", "false").casefold() == "true"
)
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

COBRANCAS_EMAIL_BACKEND = os.environ.get(
    "COBRANCAS_EMAIL_BACKEND", "console"
).casefold()
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
    if COBRANCAS_EMAIL_BACKEND == "smtp"
    else "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("COBRANCAS_EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("COBRANCAS_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("COBRANCAS_EMAIL_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("COBRANCAS_EMAIL_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("COBRANCAS_EMAIL_USE_TLS", "true").casefold() == "true"
DEFAULT_FROM_EMAIL = os.environ.get("COBRANCAS_EMAIL_FROM", "")
COBRANCAS_EMAIL_DESTINATARIOS_TESTE = tuple(
    address.strip().casefold()
    for address in os.environ.get("COBRANCAS_EMAIL_DESTINATARIOS_TESTE", "").split(",")
    if address.strip()
)
COBRANCAS_AGENDAMENTO_ENVIAR = (
    os.environ.get("COBRANCAS_AGENDAMENTO_ENVIAR", "false").casefold() == "true"
)

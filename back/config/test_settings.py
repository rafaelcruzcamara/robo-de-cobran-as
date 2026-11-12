"""Configuração isolada de testes; nunca usa o banco definido pelo operador."""

from config import settings as base_settings

for _nome in dir(base_settings):
    if not _nome.startswith("_"):
        globals()[_nome] = getattr(base_settings, _nome)

DEBUG = True
SECRET_KEY = "test-only-secret-key"
ALLOWED_HOSTS = ["testserver"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = ""

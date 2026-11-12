import os

os.environ["DJANGO_SETTINGS_MODULE"] = "config.test_settings"
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "testserver")
os.environ.setdefault("DJANGO_DEBUG", "true")

import django
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

django.setup()

from cobrancas.models import (  # noqa: E402
    Cliente,
    Cobranca,
    ConfiguracaoRegua,
    HistoricoEtapa,
)


@pytest.fixture(scope="session", autouse=True)
def criar_banco_de_teste():
    call_command("migrate", verbosity=0)


@pytest.fixture(autouse=True)
def limpar_dados():
    get_user_model().objects.all().delete()
    ConfiguracaoRegua.objects.all().delete()
    HistoricoEtapa.objects.all().delete()
    Cobranca.objects.all().delete()
    Cliente.objects.all().delete()

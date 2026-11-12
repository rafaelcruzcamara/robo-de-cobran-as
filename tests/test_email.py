from datetime import date
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from cobrancas.models import Cliente, Cobranca, ConfiguracaoRegua, HistoricoEtapa

SMTP_SETTINGS = {
    "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
    "EMAIL_HOST": "smtp.test.invalid",
    "DEFAULT_FROM_EMAIL": "robo@test.invalid",
    "COBRANCAS_EMAIL_DESTINATARIOS_TESTE": ("teste@example.com",),
}


def criar_cobranca(email="teste@example.com"):
    cliente = Cliente.objects.create(nome="Ana", email=email)
    return Cobranca.objects.create(
        cliente=cliente,
        descricao="Mensalidade",
        valor=Decimal("125.90"),
        vencimento=date(2026, 11, 20),
    )


def executar(*, enviar=False, stdout=None):
    argumentos = ["--data", "2026-11-18"]
    if enviar:
        argumentos.append("--enviar")
    call_command("processar_cobrancas", *argumentos, stdout=stdout or StringIO())


def test_simulacao_nao_grava_nem_envia_e_oculta_email():
    criar_cobranca()
    saida = StringIO()

    executar(stdout=saida)

    assert HistoricoEtapa.objects.count() == 0
    assert "Ana | Mensalidade | R$ 125,90" in saida.getvalue()
    assert "teste@example.com" not in saida.getvalue()


def test_simulacao_do_robo_nao_cria_historico_ou_configuracao():
    criar_cobranca()
    saida = StringIO()

    executar(stdout=saida)

    assert "Simulação" in saida.getvalue()
    assert HistoricoEtapa.objects.count() == 0
    assert not ConfiguracaoRegua.objects.exists()


@override_settings(**SMTP_SETTINGS)
def test_envio_autorizado_marca_enviando_antes_do_smtp_e_nao_duplica():
    criar_cobranca()

    def enviar_falso(assunto, corpo, remetente, destinatarios, **kwargs):
        assert HistoricoEtapa.objects.get().estado == HistoricoEtapa.Estado.ENVIANDO
        assert destinatarios == ["teste@example.com"]
        return 1

    with patch(
        "cobrancas.servicos_email.send_mail", side_effect=enviar_falso
    ) as enviar:
        executar(enviar=True)
        executar(enviar=True)

    assert enviar.call_count == 1
    assert HistoricoEtapa.objects.get().estado == HistoricoEtapa.Estado.ENVIADO


@override_settings(**{**SMTP_SETTINGS, "COBRANCAS_EMAIL_DESTINATARIOS_TESTE": ()})
def test_allowlist_vazia_aborta_antes_de_gravar_ou_enviar():
    criar_cobranca()

    with patch("cobrancas.servicos_email.send_mail") as enviar:
        with pytest.raises(CommandError, match="allowlist"):
            executar(enviar=True)

    enviar.assert_not_called()
    assert HistoricoEtapa.objects.count() == 0


@override_settings(**SMTP_SETTINGS)
def test_destinatario_nao_autorizado_aborta_todo_o_envio():
    criar_cobranca()
    criar_cobranca("outro@example.com")

    with patch("cobrancas.servicos_email.send_mail") as enviar:
        with pytest.raises(CommandError, match="fora da allowlist"):
            executar(enviar=True)

    enviar.assert_not_called()
    assert HistoricoEtapa.objects.count() == 0


def test_backend_padrao_recusa_envio_real():
    criar_cobranca()

    with patch("cobrancas.servicos_email.send_mail") as enviar:
        with pytest.raises(CommandError, match="backend SMTP"):
            executar(enviar=True)

    enviar.assert_not_called()
    assert HistoricoEtapa.objects.count() == 0


@override_settings(**SMTP_SETTINGS)
def test_falha_smtp_nao_e_retentada_automaticamente():
    criar_cobranca()

    with patch(
        "cobrancas.servicos_email.send_mail", side_effect=OSError("erro SMTP")
    ) as enviar:
        with pytest.raises(CommandError, match="não haverá repetição automática"):
            executar(enviar=True)
        executar(enviar=True)

    assert enviar.call_count == 1
    assert HistoricoEtapa.objects.get().estado == HistoricoEtapa.Estado.FALHOU


@pytest.mark.parametrize(
    ("data_local", "deve_executar"),
    [(date(2026, 11, 16), True), (date(2026, 11, 14), False)],
)
def test_agendamento_usa_data_local_e_ignora_fim_de_semana(data_local, deve_executar):
    with (
        patch(
            "cobrancas.management.commands.processar_cobrancas_agendado.timezone.localdate",
            return_value=data_local,
        ),
        patch(
            "cobrancas.management.commands.processar_cobrancas_agendado.call_command"
        ) as processar,
    ):
        call_command("processar_cobrancas_agendado", stdout=StringIO())

    if deve_executar:
        processar.assert_called_once()
        assert processar.call_args.args == (
            "processar_cobrancas",
            "--data",
            data_local.isoformat(),
        )
    else:
        processar.assert_not_called()


@override_settings(COBRANCAS_AGENDAMENTO_ENVIAR=False)
def test_agendamento_padrao_faz_simulacao_sem_habilitar_envio():
    data_local = date(2026, 11, 16)
    saida = StringIO()
    with (
        patch(
            "cobrancas.management.commands.processar_cobrancas_agendado.timezone.localdate",
            return_value=data_local,
        ),
        patch(
            "cobrancas.management.commands.processar_cobrancas_agendado.call_command"
        ) as processar,
    ):
        call_command("processar_cobrancas_agendado", stdout=saida)

    assert "sem envio" in saida.getvalue()
    assert "--enviar" not in processar.call_args.args


@override_settings(COBRANCAS_AGENDAMENTO_ENVIAR=True)
def test_agendamento_so_pede_envio_quando_habilitado_explicitamente():
    data_local = date(2026, 11, 16)
    with (
        patch(
            "cobrancas.management.commands.processar_cobrancas_agendado.timezone.localdate",
            return_value=data_local,
        ),
        patch(
            "cobrancas.management.commands.processar_cobrancas_agendado.call_command"
        ) as processar,
    ):
        call_command("processar_cobrancas_agendado", stdout=StringIO())

    assert "--enviar" in processar.call_args.args

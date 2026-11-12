"""Envio controlado de lembretes por e-mail."""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction

from cobrancas.models import HistoricoEtapa


def destinatarios_autorizados() -> frozenset[str]:
    """Retorna a allowlist normalizada configurada no ambiente."""
    return frozenset(
        address.strip().casefold()
        for address in settings.COBRANCAS_EMAIL_DESTINATARIOS_TESTE
        if address.strip()
    )


def validar_destinatarios(destinatarios: set[str]) -> None:
    """Falha fechada se a allowlist estiver vazia ou não autorizar todos."""
    allowlist = destinatarios_autorizados()
    if not allowlist:
        raise ValueError("allowlist de destinatários de teste não configurada")
    for destinatario in destinatarios:
        try:
            validate_email(destinatario)
        except ValidationError as exc:
            raise ValueError("destinatário cadastrado inválido") from exc
        if destinatario.strip().casefold() not in allowlist:
            raise ValueError("há destinatário fora da allowlist de teste")


def formatar_valor(valor: Decimal) -> str:
    formatado = f"{valor:,.2f}"
    return formatado.replace(",", "\0").replace(".", ",").replace("\0", ".")


def _mensagem(historico: HistoricoEtapa) -> tuple[str, str]:
    cobranca = historico.cobranca
    assunto = "Lembrete de cobrança"
    corpo = (
        f"Olá {cobranca.cliente.nome},\n\n"
        f"Este é um lembrete sobre {cobranca.descricao}, no valor de "
        f"R$ {formatar_valor(cobranca.valor)}, com vencimento em "
        f"{cobranca.vencimento:%d/%m/%Y}.\n\n"
        "Se o pagamento já foi realizado, por favor desconsidere esta mensagem.\n"
    )
    return assunto, corpo


def enviar_historico(historico_id: int) -> bool:
    """Tenta enviar uma etapa pendente uma única vez; não faz retry automático."""
    if settings.EMAIL_BACKEND != "django.core.mail.backends.smtp.EmailBackend":
        raise ValueError("backend SMTP não configurado")
    if not settings.EMAIL_HOST or not settings.DEFAULT_FROM_EMAIL:
        raise ValueError("host SMTP ou remetente não configurado")

    with transaction.atomic():
        historico = (
            HistoricoEtapa.objects.select_related("cobranca__cliente")
            .filter(pk=historico_id, estado=HistoricoEtapa.Estado.PENDENTE)
            .first()
        )
        if historico is None:
            return False
        validar_destinatarios({historico.cobranca.cliente.email})
        atualizado = HistoricoEtapa.objects.filter(
            pk=historico_id, estado=HistoricoEtapa.Estado.PENDENTE
        ).update(estado=HistoricoEtapa.Estado.ENVIANDO)
        if atualizado != 1:
            return False

    assunto, corpo = _mensagem(historico)
    try:
        enviados = send_mail(
            assunto,
            corpo,
            settings.DEFAULT_FROM_EMAIL,
            [historico.cobranca.cliente.email],
            fail_silently=False,
        )
    except Exception:
        enviados = 0

    estado = (
        HistoricoEtapa.Estado.ENVIADO if enviados == 1 else HistoricoEtapa.Estado.FALHOU
    )
    HistoricoEtapa.objects.filter(
        pk=historico_id, estado=HistoricoEtapa.Estado.ENVIANDO
    ).update(estado=estado)
    return estado == HistoricoEtapa.Estado.ENVIADO

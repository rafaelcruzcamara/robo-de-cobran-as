"""Simula ou envia etapas da régua para a data indicada."""

from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from cobrancas.models import HistoricoEtapa
from cobrancas.persistencia import etapas_devidas, registrar_etapas_pendentes
from cobrancas.servicos_email import (
    enviar_historico,
    formatar_valor,
    validar_destinatarios,
)


class Command(BaseCommand):
    help = "Simula ou envia lembretes de cobrança em uma data informada."

    def add_arguments(self, parser):
        parser.add_argument("--data", required=True, help="data da execução AAAA-MM-DD")
        parser.add_argument(
            "--enviar",
            action="store_true",
            help="envia e-mails; requer SMTP e allowlist de teste",
        )

    def handle(self, *args, **options):
        try:
            data_execucao = date.fromisoformat(options["data"])
        except ValueError as exc:
            raise CommandError("--data deve estar no formato AAAA-MM-DD") from exc
        if data_execucao.isoformat() != options["data"]:
            raise CommandError("--data deve estar no formato AAAA-MM-DD")

        devidas = etapas_devidas(data_execucao)
        if not devidas:
            self.stdout.write(
                f"Nenhum lembrete previsto para {data_execucao.isoformat()}."
            )
            return

        if not options["enviar"]:
            self.stdout.write(
                f"Simulação para {data_execucao.isoformat()} (sem gravação):"
            )
            for cobranca, etapa in devidas:
                self.stdout.write(
                    f"{cobranca.cliente.nome} | {cobranca.descricao} | "
                    f"R$ {formatar_valor(cobranca.valor)} | {etapa.value}"
                )
            return

        if settings.EMAIL_BACKEND != "django.core.mail.backends.smtp.EmailBackend":
            raise CommandError(
                "envio recusado: configure explicitamente o backend SMTP"
            )
        if not settings.EMAIL_HOST or not settings.DEFAULT_FROM_EMAIL:
            raise CommandError(
                "envio recusado: configure host SMTP e remetente no ambiente"
            )

        estados_existentes = {
            (registro.cobranca_id, registro.etapa): registro.estado
            for registro in HistoricoEtapa.objects.filter(
                cobranca_id__in=[cobranca.pk for cobranca, _ in devidas]
            )
        }
        pendentes = [
            cobranca
            for cobranca, etapa in devidas
            if estados_existentes.get((cobranca.pk, etapa.value))
            in (None, HistoricoEtapa.Estado.PENDENTE)
        ]
        try:
            validar_destinatarios({cobranca.cliente.email for cobranca in pendentes})
        except ValueError as exc:
            raise CommandError(f"envio recusado: {exc}") from exc

        historicos = registrar_etapas_pendentes(data_execucao)
        ids_pendentes = [
            historico.pk
            for historico, _ in historicos
            if historico.estado == HistoricoEtapa.Estado.PENDENTE
        ]
        enviados = sum(enviar_historico(pk) for pk in ids_pendentes)
        falhas = len(ids_pendentes) - enviados
        self.stdout.write(f"Enviados: {enviados}; falhas: {falhas}.")
        if falhas:
            raise CommandError(
                "um ou mais envios falharam; não haverá repetição automática"
            )

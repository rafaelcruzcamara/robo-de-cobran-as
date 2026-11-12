"""Executa a simulação diária ou o envio explicitamente habilitado."""

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.utils import timezone


class Command(BaseCommand):
    help = "Processa a régua em dia útil usando a data local de São Paulo."

    def handle(self, *args, **options):
        hoje = timezone.localdate()
        if hoje.weekday() >= 5:
            self.stdout.write(
                f"Execução ignorada em fim de semana ({hoje.isoformat()})."
            )
            return

        argumentos = ["--data", hoje.isoformat()]
        if settings.COBRANCAS_AGENDAMENTO_ENVIAR:
            argumentos.append("--enviar")
            self.stdout.write(f"Processando envio agendado para {hoje.isoformat()}.")
        else:
            self.stdout.write(
                f"Modo simulação agendada para {hoje.isoformat()} (sem envio)."
            )
        call_command("processar_cobrancas", *argumentos, stdout=self.stdout)

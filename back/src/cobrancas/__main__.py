"""Ponto de entrada da interface de linha de comando."""

import argparse
import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from cobrancas.importacao import ResultadoImportacao, ler_csv, ler_xlsx
from cobrancas.regras import EtapaCobranca, avaliar_cobranca


def _formatar_valor(valor: Decimal) -> str:
    formatado = f"{valor:,.2f}"
    return formatado.replace(",", "\0").replace(".", ",").replace("\0", ".")


def _ler_arquivo(caminho: Path) -> ResultadoImportacao:
    extensao = caminho.suffix.casefold()
    conteudo = caminho.read_bytes()
    if extensao == ".csv":
        return ler_csv(conteudo.decode("utf-8-sig"))
    if extensao == ".xlsx":
        return ler_xlsx(conteudo)
    raise ValueError("extensão não suportada; use .csv ou .xlsx")


def _intervalos_regua() -> tuple[int, int]:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    from django.apps import apps

    if not apps.ready:
        django.setup()
    from cobrancas.models import ConfiguracaoRegua

    configuracao = ConfiguracaoRegua.objects.filter(pk=1).first()
    if configuracao is None:
        return 2, 7
    return configuracao.dias_antes, configuracao.dias_depois


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m cobrancas")
    subcomandos = parser.add_subparsers(dest="comando", required=True)
    simular = subcomandos.add_parser("simular", help="simula lembretes sem enviá-los")
    simular.add_argument("arquivo", type=Path)
    simular.add_argument(
        "--data", required=True, help="data da simulação no formato AAAA-MM-DD"
    )
    simular.add_argument("--dias-antes", type=int)
    simular.add_argument("--dias-depois", type=int)
    argumentos = parser.parse_args(argv)

    for intervalo in (argumentos.dias_antes, argumentos.dias_depois):
        if intervalo is not None and not 1 <= intervalo <= 365:
            print(
                "Erro: os intervalos devem estar entre 1 e 365 dias.",
                file=sys.stderr,
            )
            return 2

    try:
        data_simulacao = date.fromisoformat(argumentos.data)
    except ValueError:
        print("Erro: --data deve estar no formato AAAA-MM-DD.", file=sys.stderr)
        return 2

    try:
        dias_antes_configurados, dias_depois_configurados = _intervalos_regua()
    except Exception:
        print(
            "Erro: não foi possível ler a régua configurada; "
            "aplique as migrações do banco.",
            file=sys.stderr,
        )
        return 2
    dias_antes = argumentos.dias_antes or dias_antes_configurados
    dias_depois = argumentos.dias_depois or dias_depois_configurados
    if not 1 <= dias_antes <= 365 or not 1 <= dias_depois <= 365:
        print("Erro: os intervalos devem estar entre 1 e 365 dias.", file=sys.stderr)
        return 2

    try:
        resultado = _ler_arquivo(argumentos.arquivo)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2

    if resultado.erros:
        for erro in resultado.erros:
            print(
                f"Linha {erro.linha}, campo {erro.campo}: {erro.mensagem}",
                file=sys.stderr,
            )
        return 2

    lembretes = []
    for cobranca in resultado.cobrancas:
        etapa = avaliar_cobranca(
            cobranca.vencimento,
            data_simulacao,
            paga=cobranca.paga,
            pausada=cobranca.pausada,
            dias_antes=dias_antes,
            dias_depois=dias_depois,
        )
        if etapa is not None:
            lembretes.append((cobranca, etapa))

    print(f"Simulação para {data_simulacao.isoformat()}")
    if not lembretes:
        print("Nenhum lembrete previsto.")
        return 0

    for cobranca, etapa in lembretes:
        nome_etapa = {
            EtapaCobranca.PRE_VENCIMENTO: (f"{dias_antes} dias antes do vencimento"),
            EtapaCobranca.VENCIMENTO: "no vencimento",
            EtapaCobranca.ATRASO_7_DIAS: (f"{dias_depois} dias após o vencimento"),
        }[etapa]
        print(
            f"{cobranca.cliente} | {cobranca.descricao} | "
            f"R$ {_formatar_valor(cobranca.valor)} | {nome_etapa}"
        )
    print(f"Total de lembretes: {len(lembretes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

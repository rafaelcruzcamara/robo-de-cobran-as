"""Leitura e validação de arquivos de cobranças, sem persistência."""

import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

CABECALHOS = (
    "cliente",
    "email",
    "descricao",
    "valor",
    "vencimento",
    "pago",
    "pausado",
)
_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_VALOR_CSV = re.compile(r"^\d+(?:,\d{1,2})?$")


@dataclass(frozen=True)
class CobrancaImportada:
    cliente: str
    email: str
    descricao: str
    valor: Decimal
    vencimento: date
    paga: bool
    pausada: bool


@dataclass(frozen=True)
class ErroImportacao:
    linha: int
    campo: str
    mensagem: str


@dataclass(frozen=True)
class ResultadoImportacao:
    cobrancas: tuple[CobrancaImportada, ...]
    erros: tuple[ErroImportacao, ...]


def _texto(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _booleano(valor: Any) -> bool:
    if isinstance(valor, bool):
        return valor
    texto = _texto(valor).casefold()
    if texto in {"sim", "s", "true", "1"}:
        return True
    if texto in {"não", "nao", "n", "false", "0"}:
        return False
    raise ValueError("use sim/não ou verdadeiro/falso")


def _valor_decimal(valor: Any, csv_localizado: bool) -> Decimal:
    if isinstance(valor, bool) or valor is None:
        raise ValueError("valor monetário inválido")
    texto = _texto(valor)
    if csv_localizado:
        if not _VALOR_CSV.fullmatch(texto):
            raise ValueError("use número com vírgula decimal, por exemplo 1234,56")
        texto = texto.replace(",", ".")
    try:
        decimal = Decimal(texto)
    except InvalidOperation as exc:
        raise ValueError("valor monetário inválido") from exc
    if not decimal.is_finite() or decimal <= 0 or decimal.as_tuple().exponent < -2:
        raise ValueError("o valor deve ser positivo e ter no máximo 2 casas decimais")
    return decimal


def _data(valor: Any, csv_localizada: bool) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = _texto(valor)
    try:
        return (
            datetime.strptime(texto, "%d/%m/%Y").date()
            if csv_localizada
            else date.fromisoformat(texto)
        )
    except ValueError as exc:
        formato = "DD/MM/AAAA" if csv_localizada else "data válida do Excel"
        raise ValueError(f"use {formato}") from exc


def _validar_linhas(
    linhas: list[tuple[int, dict[str, Any]]], csv_localizada: bool
) -> ResultadoImportacao:
    cobrancas: list[CobrancaImportada] = []
    erros: list[ErroImportacao] = []
    for numero, linha in linhas:
        valores: dict[str, Any] = {}
        for campo in CABECALHOS:
            bruto = linha.get(campo)
            try:
                if campo in {"cliente", "descricao"}:
                    valor = _texto(bruto)
                    if not valor:
                        raise ValueError("campo obrigatório")
                elif campo == "email":
                    valor = _texto(bruto)
                    if not _EMAIL.fullmatch(valor):
                        raise ValueError("e-mail inválido")
                elif campo == "valor":
                    valor = _valor_decimal(bruto, csv_localizada)
                elif campo == "vencimento":
                    valor = _data(bruto, csv_localizada)
                else:
                    valor = _booleano(bruto)
                valores[campo] = valor
            except ValueError as exc:
                erros.append(ErroImportacao(numero, campo, str(exc)))
        if not any(erro.linha == numero for erro in erros):
            cobrancas.append(
                CobrancaImportada(
                    cliente=valores["cliente"],
                    email=valores["email"],
                    descricao=valores["descricao"],
                    valor=valores["valor"],
                    vencimento=valores["vencimento"],
                    paga=valores["pago"],
                    pausada=valores["pausado"],
                )
            )
    return ResultadoImportacao(tuple(cobrancas), tuple(erros))


def ler_csv(conteudo: str) -> ResultadoImportacao:
    """Lê CSV UTF-8 separado por ponto e vírgula e valida cada linha."""
    try:
        leitor = csv.reader(
            io.StringIO(conteudo, newline=""), delimiter=";", strict=True
        )
        cabecalho = next(leitor)
    except (csv.Error, StopIteration):
        return ResultadoImportacao(
            (), (ErroImportacao(1, "arquivo", "arquivo vazio ou CSV inválido"),)
        )
    cabecalho = [item.lstrip("\ufeff").strip().casefold() for item in cabecalho]
    if len(cabecalho) != len(set(cabecalho)):
        return ResultadoImportacao(
            (), (ErroImportacao(1, "cabecalho", "colunas duplicadas"),)
        )
    if set(cabecalho) != set(CABECALHOS):
        return ResultadoImportacao(
            (),
            (
                ErroImportacao(
                    1, "cabecalho", "colunas obrigatórias ausentes ou inesperadas"
                ),
            ),
        )
    linhas: list[tuple[int, dict[str, Any]]] = []
    try:
        for numero, valores in enumerate(leitor, start=2):
            if len(valores) != len(cabecalho):
                return ResultadoImportacao(
                    (),
                    (
                        ErroImportacao(
                            numero,
                            "linha",
                            "quantidade de campos diferente do cabeçalho",
                        ),
                    ),
                )
            linhas.append((numero, dict(zip(cabecalho, valores, strict=True))))
    except csv.Error:
        return ResultadoImportacao(
            (), (ErroImportacao(1, "arquivo", "estrutura CSV inválida"),)
        )
    if not linhas:
        return ResultadoImportacao(
            (), (ErroImportacao(2, "arquivo", "nenhum registro encontrado"),)
        )
    return _validar_linhas(linhas, csv_localizada=True)


def ler_xlsx(conteudo: bytes) -> ResultadoImportacao:
    """Lê a primeira planilha XLSX e valida seus registros."""
    try:
        livro = load_workbook(io.BytesIO(conteudo), read_only=True, data_only=True)
    except (BadZipFile, InvalidFileException, OSError, ValueError):
        return ResultadoImportacao(
            (), (ErroImportacao(1, "arquivo", "arquivo XLSX inválido"),)
        )
    try:
        planilha = livro.active
        linhas_planilha = planilha.iter_rows(values_only=True)
        cabecalho_original = next(linhas_planilha, None)
        if not cabecalho_original:
            return ResultadoImportacao(
                (), (ErroImportacao(1, "arquivo", "planilha vazia"),)
            )
        cabecalho = [_texto(item).casefold() for item in cabecalho_original]
        if len(cabecalho) != len(set(cabecalho)):
            return ResultadoImportacao(
                (), (ErroImportacao(1, "cabecalho", "colunas duplicadas"),)
            )
        if set(cabecalho) != set(CABECALHOS):
            return ResultadoImportacao(
                (),
                (
                    ErroImportacao(
                        1, "cabecalho", "colunas obrigatórias ausentes ou inesperadas"
                    ),
                ),
            )
        linhas = []
        for numero, valores in enumerate(linhas_planilha, start=2):
            if all(valor is None for valor in valores):
                continue
            if len(valores) != len(cabecalho):
                return ResultadoImportacao(
                    (),
                    (
                        ErroImportacao(
                            numero,
                            "linha",
                            "quantidade de campos diferente do cabeçalho",
                        ),
                    ),
                )
            linhas.append((numero, dict(zip(cabecalho, valores, strict=True))))
        if not linhas:
            return ResultadoImportacao(
                (), (ErroImportacao(2, "arquivo", "nenhum registro encontrado"),)
            )
        return _validar_linhas(linhas, csv_localizada=False)
    finally:
        livro.close()

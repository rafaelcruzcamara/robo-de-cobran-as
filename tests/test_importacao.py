from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

from openpyxl import Workbook

from cobrancas.importacao import CABECALHOS, ler_csv, ler_xlsx

CSV_VALIDO = (
    "cliente;email;descricao;valor;vencimento;pago;pausado\n"
    "Ana;ana@example.com;Mensalidade;1234,56;20/11/2026;não;não\n"
)


def test_importa_csv_com_dados_brasileiros():
    resultado = ler_csv(CSV_VALIDO)

    assert resultado.erros == ()
    assert resultado.cobrancas[0].valor == Decimal("1234.56")
    assert resultado.cobrancas[0].vencimento == date(2026, 11, 20)
    assert resultado.cobrancas[0].paga is False


def test_csv_retorna_erros_por_linha_e_campo_sem_perder_linhas_validas():
    conteudo = CSV_VALIDO + "Bia;email-invalido;Mensalidade;10,00;31/02/2026;não;não\n"

    resultado = ler_csv(conteudo)

    assert len(resultado.cobrancas) == 1
    assert {(erro.linha, erro.campo) for erro in resultado.erros} == {
        (3, "email"),
        (3, "vencimento"),
    }


def test_csv_rejeita_cabecalho_duplicado():
    resultado = ler_csv("cliente;cliente\nAna;Bia")

    assert resultado.cobrancas == ()
    assert resultado.erros[0].campo == "cabecalho"


def test_csv_aceita_bom_utf8_e_rejeita_aspas_malformadas():
    assert len(ler_csv("\ufeff" + CSV_VALIDO).cobrancas) == 1
    resultado = ler_csv(CSV_VALIDO + '"registro sem fechamento')

    assert resultado.cobrancas == ()
    assert resultado.erros[0].campo == "arquivo"


def test_importa_xlsx_com_celulas_nativas():
    livro = Workbook()
    planilha = livro.active
    planilha.append(CABECALHOS)
    planilha.append(
        [
            "Ana",
            "ana@example.com",
            "Mensalidade",
            1234.56,
            datetime(2026, 11, 20),
            False,
            True,
        ]
    )
    conteudo = BytesIO()
    livro.save(conteudo)

    resultado = ler_xlsx(conteudo.getvalue())

    assert resultado.erros == ()
    assert resultado.cobrancas[0].valor == Decimal("1234.56")
    assert resultado.cobrancas[0].vencimento == date(2026, 11, 20)
    assert resultado.cobrancas[0].pausada is True


def test_xlsx_invalido_retorna_erro_sem_expor_conteudo():
    resultado = ler_xlsx(b"nao e um xlsx")

    assert resultado.cobrancas == ()
    assert resultado.erros[0].campo == "arquivo"

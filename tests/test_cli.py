from cobrancas.__main__ import main
from cobrancas.models import ConfiguracaoRegua

CSV_COBRANCA = (
    "cliente;email;descricao;valor;vencimento;pago;pausado\n"
    "Ana;ana-secreta@example.com;Mensalidade;1234,56;20/11/2026;não;não\n"
)


def test_simulacao_exibe_etapa_sem_exibir_email(tmp_path, capsys):
    arquivo = tmp_path / "cobrancas.csv"
    arquivo.write_text(CSV_COBRANCA, encoding="utf-8")

    codigo = main(["simular", str(arquivo), "--data", "2026-11-18"])

    saida = capsys.readouterr()
    assert codigo == 0
    assert "Ana | Mensalidade | R$ 1.234,56 | 2 dias antes do vencimento" in saida.out
    assert "ana-secreta@example.com" not in saida.out
    assert saida.err == ""


def test_simulacao_com_data_sem_lembrete(tmp_path, capsys):
    arquivo = tmp_path / "cobrancas.csv"
    arquivo.write_text(CSV_COBRANCA, encoding="utf-8")

    codigo = main(["simular", str(arquivo), "--data", "2026-11-19"])

    assert codigo == 0
    assert "Nenhum lembrete previsto." in capsys.readouterr().out


def test_importacao_com_erros_aborta_sem_simular(tmp_path, capsys):
    arquivo = tmp_path / "cobrancas.csv"
    arquivo.write_text(
        CSV_COBRANCA.replace("ana-secreta@example.com", "email-invalido"),
        encoding="utf-8",
    )

    codigo = main(["simular", str(arquivo), "--data", "2026-11-18"])

    saida = capsys.readouterr()
    assert codigo == 2
    assert "Linha 2, campo email" in saida.err
    assert saida.out == ""


def test_data_invalida_retorna_codigo_de_erro(tmp_path, capsys):
    arquivo = tmp_path / "cobrancas.csv"

    codigo = main(["simular", str(arquivo), "--data", "18/11/2026"])

    saida = capsys.readouterr()
    assert codigo == 2
    assert "AAAA-MM-DD" in saida.err


def test_simulacao_aceita_intervalos_configurados(tmp_path, capsys):
    arquivo = tmp_path / "cobrancas.csv"
    arquivo.write_text(CSV_COBRANCA, encoding="utf-8")

    codigo = main(
        [
            "simular",
            str(arquivo),
            "--data",
            "2026-11-17",
            "--dias-antes",
            "3",
        ]
    )

    saida = capsys.readouterr()
    assert codigo == 0
    assert "3 dias antes do vencimento" in saida.out


def test_simulacao_usa_regua_salva_quando_nao_sobrescrita(tmp_path, capsys):
    arquivo = tmp_path / "cobrancas.csv"
    arquivo.write_text(CSV_COBRANCA, encoding="utf-8")
    ConfiguracaoRegua.objects.create(dias_antes=3, dias_depois=10)

    codigo = main(["simular", str(arquivo), "--data", "2026-11-17"])

    saida = capsys.readouterr()
    assert codigo == 0
    assert "3 dias antes do vencimento" in saida.out

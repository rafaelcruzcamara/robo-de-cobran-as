from datetime import date, timedelta

import pytest

from cobrancas.regras import EtapaCobranca, avaliar_cobranca


@pytest.mark.parametrize(
    ("dias_ate_vencimento", "etapa"),
    [
        (2, EtapaCobranca.PRE_VENCIMENTO),
        (0, EtapaCobranca.VENCIMENTO),
        (-7, EtapaCobranca.ATRASO_7_DIAS),
    ],
)
def test_retorna_etapa_nas_datas_da_regua(dias_ate_vencimento, etapa):
    vencimento = date(2026, 11, 20)
    hoje = vencimento - timedelta(days=dias_ate_vencimento)

    assert avaliar_cobranca(vencimento, hoje) is etapa


@pytest.mark.parametrize("dias_ate_vencimento", [3, 1, -1, -6, -8, 30])
def test_nao_retorna_etapa_fora_das_datas_da_regua(dias_ate_vencimento):
    vencimento = date(2026, 11, 20)
    hoje = vencimento - timedelta(days=dias_ate_vencimento)

    assert avaliar_cobranca(vencimento, hoje) is None


@pytest.mark.parametrize("estado", [{"paga": True}, {"pausada": True}])
def test_nao_cobra_cliente_pago_ou_pausado(estado):
    vencimento = date(2026, 11, 20)

    assert avaliar_cobranca(vencimento, vencimento, **estado) is None


def test_intervalos_da_regua_podem_ser_configurados():
    vencimento = date(2026, 11, 20)

    assert (
        avaliar_cobranca(vencimento, date(2026, 11, 16), dias_antes=4, dias_depois=10)
        is EtapaCobranca.PRE_VENCIMENTO
    )
    assert (
        avaliar_cobranca(vencimento, date(2026, 11, 30), dias_antes=4, dias_depois=10)
        is EtapaCobranca.ATRASO_7_DIAS
    )


@pytest.mark.parametrize("dias_antes,dias_depois", [(0, 7), (2, -1)])
def test_intervalos_invalidos_sao_rejeitados(dias_antes, dias_depois):
    with pytest.raises(ValueError):
        avaliar_cobranca(
            date(2026, 11, 20),
            date(2026, 11, 18),
            dias_antes=dias_antes,
            dias_depois=dias_depois,
        )

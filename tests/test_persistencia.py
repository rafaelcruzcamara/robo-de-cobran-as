from datetime import date
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from cobrancas.models import Cliente, Cobranca, ConfiguracaoRegua, HistoricoEtapa
from cobrancas.persistencia import etapas_devidas, registrar_etapas_pendentes
from cobrancas.regras import EtapaCobranca


def criar_cobranca(*, pausado=False, baixada_em=None, paga=False):
    cliente = Cliente.objects.create(
        nome="Cliente de teste", email="teste@example.com", pausado=pausado
    )
    return Cobranca.objects.create(
        cliente=cliente,
        descricao="Fatura fictícia",
        valor=Decimal("125.90"),
        vencimento=date(2026, 11, 20),
        paga=paga,
        baixada_em=baixada_em,
    )


def test_registrar_etapas_e_idempotente():
    cobranca = criar_cobranca()

    primeira_execucao = registrar_etapas_pendentes(date(2026, 11, 18))
    segunda_execucao = registrar_etapas_pendentes(date(2026, 11, 18))

    assert len(primeira_execucao) == 1
    assert primeira_execucao[0][1] is True
    assert len(segunda_execucao) == 1
    assert segunda_execucao[0][1] is False
    assert HistoricoEtapa.objects.filter(cobranca=cobranca).count() == 1
    assert HistoricoEtapa.objects.get().estado == HistoricoEtapa.Estado.PENDENTE


def test_execucao_usa_intervalos_persistidos():
    cobranca = criar_cobranca()
    ConfiguracaoRegua.objects.create(dias_antes=4, dias_depois=10)

    resultado = etapas_devidas(date(2026, 11, 16))

    assert resultado == [(cobranca, EtapaCobranca.PRE_VENCIMENTO)]


def test_historico_mostra_o_intervalo_efetivamente_aplicado():
    criar_cobranca()
    ConfiguracaoRegua.objects.create(dias_antes=4, dias_depois=10)
    historico, _ = registrar_etapas_pendentes(date(2026, 11, 16))[0]

    assert historico.descricao_etapa == "Pré-vencimento (4 dias)"


def test_alterar_regua_preserva_etapa_ja_registrada():
    cobranca = criar_cobranca()
    original = registrar_etapas_pendentes(date(2026, 11, 18))[0][0]
    ConfiguracaoRegua.objects.create(dias_antes=3, dias_depois=10)

    resultado = registrar_etapas_pendentes(date(2026, 11, 17))

    assert resultado[0][0].pk == original.pk
    assert resultado[0][1] is False
    assert HistoricoEtapa.objects.filter(cobranca=cobranca).count() == 1
    assert original.data_execucao == date(2026, 11, 18)


def test_constraint_do_banco_rejeita_intervalo_fora_da_faixa():
    with pytest.raises(IntegrityError), transaction.atomic():
        ConfiguracaoRegua.objects.create(dias_antes=0, dias_depois=7)


@pytest.mark.parametrize(
    "estado",
    [
        {"pausado": True},
        {"baixada_em": date(2026, 11, 17)},
        {"paga": True},
    ],
)
def test_nao_registra_etapa_para_cliente_pausado_ou_cobranca_paga(estado):
    criar_cobranca(**estado)

    resultado = registrar_etapas_pendentes(date(2026, 11, 18))

    assert resultado == []
    assert HistoricoEtapa.objects.count() == 0


def test_transacao_externa_reverte_etapas_se_operacao_abortar():
    criar_cobranca()

    with pytest.raises(RuntimeError), transaction.atomic():
        registrar_etapas_pendentes(date(2026, 11, 18))
        raise RuntimeError("falha simulada")

    assert HistoricoEtapa.objects.count() == 0


def test_restricao_do_banco_impede_etapa_duplicada():
    cobranca = criar_cobranca()
    registrar_etapas_pendentes(date(2026, 11, 18))

    with pytest.raises(IntegrityError):
        HistoricoEtapa.objects.create(
            cobranca=cobranca,
            etapa=HistoricoEtapa.Etapa.PRE_VENCIMENTO,
            data_execucao=date(2026, 11, 18),
        )

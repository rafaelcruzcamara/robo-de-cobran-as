"""Operações transacionais de persistência para o motor de cobrança."""

from datetime import date

from django.db import transaction

from cobrancas.models import Cobranca, ConfiguracaoRegua, HistoricoEtapa
from cobrancas.regras import EtapaCobranca, avaliar_cobranca

_ETAPA_PERSISTIDA = {
    EtapaCobranca.PRE_VENCIMENTO: HistoricoEtapa.Etapa.PRE_VENCIMENTO,
    EtapaCobranca.VENCIMENTO: HistoricoEtapa.Etapa.VENCIMENTO,
    EtapaCobranca.ATRASO_7_DIAS: HistoricoEtapa.Etapa.ATRASO_7_DIAS,
}


def etapas_devidas(data_execucao: date) -> list[tuple[Cobranca, EtapaCobranca]]:
    """Retorna cobranças elegíveis e suas etapas para a data informada."""
    resultados = []
    configuracao = ConfiguracaoRegua.objects.filter(pk=1).first()
    dias_antes = configuracao.dias_antes if configuracao else 2
    dias_depois = configuracao.dias_depois if configuracao else 7
    cobrancas = Cobranca.objects.select_related("cliente").filter(
        paga=False,
        cliente__pausado=False,
    )
    for cobranca in cobrancas.iterator():
        etapa = avaliar_cobranca(
            cobranca.vencimento,
            data_execucao,
            paga=cobranca.paga,
            pausada=cobranca.cliente.pausado,
            dias_antes=dias_antes,
            dias_depois=dias_depois,
        )
        if etapa is not None:
            resultados.append((cobranca, etapa))
    return resultados


@transaction.atomic
def registrar_etapas_pendentes(
    data_execucao: date,
) -> list[tuple[HistoricoEtapa, bool]]:
    """Registra etapas devidas hoje; retorna cada histórico e se foi criado."""
    resultados = []
    for cobranca, etapa in etapas_devidas(data_execucao):
        historico, criado = HistoricoEtapa.objects.get_or_create(
            cobranca=cobranca,
            etapa=_ETAPA_PERSISTIDA[etapa],
            defaults={"data_execucao": data_execucao},
        )
        resultados.append((historico, criado))
    return resultados

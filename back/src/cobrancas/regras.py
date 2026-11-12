"""Regras puras para determinar etapas de lembretes de cobrança."""

from datetime import date
from enum import Enum


class EtapaCobranca(Enum):
    """Etapas da régua inicial, definidas em dias corridos."""

    PRE_VENCIMENTO = "pre_vencimento"
    VENCIMENTO = "vencimento"
    ATRASO_7_DIAS = "atraso_7_dias"


def avaliar_cobranca(
    vencimento: date,
    hoje: date,
    *,
    paga: bool = False,
    pausada: bool = False,
    dias_antes: int = 2,
    dias_depois: int = 7,
) -> EtapaCobranca | None:
    """Retorna a etapa devida hoje, ou ``None`` se não houver lembrete.

    A régua dispara no offset configurado antes, no vencimento e no offset
    configurado depois. Os padrões são 2 dias antes e 7 dias depois.
    Datas passadas não são recuperadas. Pagamento e pausa bloqueiam os avisos.
    """
    if paga or pausada:
        return None
    if dias_antes < 1 or dias_depois < 1:
        raise ValueError("os intervalos devem ser maiores que zero")

    dias_ate_vencimento = (vencimento - hoje).days
    if dias_ate_vencimento == dias_antes:
        return EtapaCobranca.PRE_VENCIMENTO
    if dias_ate_vencimento == 0:
        return EtapaCobranca.VENCIMENTO
    if dias_ate_vencimento == -dias_depois:
        return EtapaCobranca.ATRASO_7_DIAS
    return None

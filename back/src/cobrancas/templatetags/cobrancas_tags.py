"""Filtros para valores monetários apresentados em pt-BR."""

from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def brl(valor: Decimal) -> str:
    formatado = f"{valor:,.2f}"
    return formatado.replace(",", "\0").replace(".", ",").replace("\0", ".")

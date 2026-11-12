# SPEC — Motor inicial de regras de cobrança

## Objetivo

Determinar se uma cobrança deve gerar uma etapa de lembrete em uma data informada, sem acessar relógio, banco de dados ou rede.

## Escopo

Inclui uma função pura que identifica lembretes 2 dias antes do vencimento, no vencimento e 7 dias após o vencimento. Cobranças pagas ou clientes pausados não geram etapa. Não inclui envio, persistência, dias úteis, feriados nem configuração da régua.

## Plano de execução

1. Implementar os tipos e a função pura em `back/src/cobrancas/regras.py`.
2. Cobrir as três datas da régua, datas sem etapa e bloqueios por pagamento/pausa.
3. Rodar testes, Ruff e revisar o diff.

## Critérios de aceite

- A data atual é sempre recebida como argumento.
- A função retorna a etapa somente nas datas previstas.
- Pagamento baixado ou cliente pausado bloqueia qualquer etapa.
- Testes automatizados cobrem os três disparos e casos sem disparo.

## Riscos

Disparos em dias corridos não consideram fins de semana ou feriados. As datas são exatas: não há recuperação de etapas passadas.

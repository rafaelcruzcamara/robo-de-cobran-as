# ADR-0001 — Framework web

## Contexto

O MVP precisa de uma interface web renderizada no servidor, autenticação e acesso a banco de dados. O projeto é um portfólio backend em Python, sem frontend separado.

## Decisão

Usar Django como framework web.

## Alternativas consideradas

- FastAPI: excelente para APIs, mas exigiria escolher e integrar mais componentes para templates e autenticação neste escopo.
- Django: inclui estrutura integrada para aplicações web renderizadas no servidor e atende ao formato do MVP.

## Consequências

Django concentra a aplicação web em uma stack Python integrada e reduz escolhas iniciais. Será necessário aprender as convenções próprias do framework. A decisão poderá ser revisada se os requisitos mudarem.

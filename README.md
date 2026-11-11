# Robô de cobrança

Pequenas empresas podem perder tempo conferindo planilhas e escrevendo cobranças manualmente. Este projeto busca automatizar lembretes respeitosos, registrar cada ação e deixar claro quando um caso precisa de atenção humana.

## Escopo aprovado do MVP

- Aplicação web em Django, com páginas renderizadas no servidor.
- Importação de cobranças por CSV e Excel, além de cadastro pela interface.
- Régua de cobrança configurável e modo de simulação.
- Histórico de envios idempotente; baixa de pagamento e pausa de cliente.
- Painel com valores e ações recentes.
- Execução do robô manual por comando; agendamento fica para fase posterior.
- Envio de e-mail real restrito a endereços de teste autorizados.
- SQLite no desenvolvimento e PostgreSQL como alvo de produção.

## Estado atual

Fase 0 — preparação do ambiente. A aplicação e suas funcionalidades serão construídas nas fases seguintes.

## Desenvolvimento

Requer Python 3.12 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
```

No PowerShell, caso a ativação do ambiente virtual seja bloqueada pela política local, use os executáveis diretamente: `.venv\Scripts\python.exe` e `.venv\Scripts\pytest.exe`.

## Limitações conhecidas

- Ainda não há aplicação web, persistência, importação ou envio implementados.
- O uso com cobranças reais depende de decisões operacionais, revisão de segurança e validação profissional das obrigações legais aplicáveis.

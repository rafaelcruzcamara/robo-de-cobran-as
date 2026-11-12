# Robô de cobrança

Pequenas empresas podem perder tempo conferindo planilhas e escrevendo cobranças manualmente. Este projeto busca automatizar lembretes respeitosos, registrar cada ação e deixar claro quando um caso precisa de atenção humana.

## Escopo aprovado do MVP

- Aplicação web em Django, com páginas renderizadas no servidor.
- Importação de cobranças por CSV e Excel, além de cadastro pela interface.
- Régua de cobrança configurável e modo de simulação.
- Histórico de envios idempotente; baixa de pagamento e pausa de cliente.
- Painel com valores e ações recentes.
- Rotina de agendamento preparada para a Render; simula por padrão e só envia quando habilitada explicitamente.
- Envio de e-mail real restrito a endereços de teste autorizados.
- SQLite no desenvolvimento e PostgreSQL como alvo de produção.

## Estado atual

O núcleo do MVP está implementado e separado em `front/` e `back/`. O código foi enviado ao GitHub, mas não há hospedagem paga nem deploy. A opção escolhida para tentar entrega sem custo é uma conta Gmail pessoal usada localmente; ainda faltam o endereço remetente e a configuração da senha de app. O envio permanece desativado e o site de demonstração usa banco temporário isolado.

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

Para desenvolvimento local, habilite o modo local e prepare o banco/usuário:

```powershell
$env:DJANGO_DEBUG = "true"
python back/manage.py migrate
python back/manage.py createsuperuser
python back/manage.py runserver
```

Com `DJANGO_DEBUG=false` (padrão), o Django exige `DJANGO_SECRET_KEY`; configure uma chave forte fora do repositório.

Com o servidor em execução, acesse `http://127.0.0.1:8000/` e entre com o usuário criado por `createsuperuser`. O painel oferece cadastro de clientes/cobranças, baixa de pagamento, pausa de cliente e importação CSV/XLSX com prévia antes de gravar. A importação aceita arquivos de até 5 MB e exige reenviar o mesmo arquivo para confirmar.

As datas locais do painel e a sugestão de baixa usam o fuso `America/Sao_Paulo`.

Na opção **Régua**, ajuste os dias corridos antes e depois do vencimento (de 1 a 365). Os valores iniciais são 2 e 7 dias; a etapa no vencimento permanece fixa. Alterações não apagam o histórico registrado.

Para simular lembretes sem enviar mensagens:

```powershell
python -m cobrancas simular cobrancas.csv --data 2026-11-18
python -m cobrancas simular cobrancas.csv --data 2026-11-17 --dias-antes 3 --dias-depois 10
python back/manage.py processar_cobrancas --data 2026-11-18
```

Sem os parâmetros `--dias-antes`/`--dias-depois`, o simulador de arquivo lê os valores guardados na tela **Régua**. O comando Django consulta as cobranças persistidas e a régua configurada; sem `--enviar`, não grava histórico nem envia e-mails. Para habilitar envio real, configure no ambiente `COBRANCAS_EMAIL_BACKEND=smtp`, `COBRANCAS_EMAIL_HOST`, `COBRANCAS_EMAIL_FROM` e `COBRANCAS_EMAIL_DESTINATARIOS_TESTE` (lista separada por vírgulas). Também estão disponíveis `COBRANCAS_EMAIL_PORT` (padrão 587), `COBRANCAS_EMAIL_USER`, `COBRANCAS_EMAIL_PASSWORD` e `COBRANCAS_EMAIL_USE_TLS` (padrão true). Em seguida, `python back/manage.py processar_cobrancas --data 2026-11-18 --enviar` envia somente se todos os destinatários estiverem na allowlist. Não coloque credenciais no repositório.

Para preparar uma instalação PostgreSQL, instale o extra `python -m pip install -e ".[postgres]"` e configure `COBRANCAS_DB_ENGINE=postgresql`, `COBRANCAS_DB_NAME`, `COBRANCAS_DB_USER`, `COBRANCAS_DB_PASSWORD`, `COBRANCAS_DB_HOST` e opcionalmente `COBRANCAS_DB_PORT`/`COBRANCAS_DB_SSLMODE`; depois execute `python back/manage.py migrate`. SQLite continua sendo o padrão local. O workflow em `.github/workflows/ci.yml` aplica as migrações em PostgreSQL e executa a suíte isolada em SQLite. Veja `docs/operacao-producao.md` para o Blueprint da Render, limites, variáveis e preparação do job agendado.

## Limitações conhecidas

- A aplicação ainda não foi publicada nem validada em uma conta Render. O Blueprint usa planos pagos para web, cron e banco; revise preços, região, domínio, backups e requisitos operacionais no painel antes de criar recursos. Para manter deployments controlados, o auto-deploy está desligado.
- O job hospedado está configurado para simular em dias úteis às 09:00 de São Paulo. Para envio, é necessário configurar SMTP e allowlist apenas com endereços de teste e, depois de validá-los, habilitar `COBRANCAS_AGENDAMENTO_ENVIAR=true` deliberadamente. Não habilite para clientes reais sem decisão operacional separada.
- O uso com cobranças reais depende de decisões operacionais, revisão de segurança e validação profissional das obrigações legais aplicáveis.

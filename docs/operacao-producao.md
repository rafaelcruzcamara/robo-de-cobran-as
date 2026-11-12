# Operação e preparação de produção

O arquivo `render.yaml` prepara uma implantação na Render com PostgreSQL, Gunicorn, WhiteNoise e job de cron. Não sincronize o Blueprint antes de revisar custos, nome/domínio, região, backups e limites dos planos no painel.

## Estado atual e ponto de retomada

- O usuário escolheu **Gmail pessoal** para experimentar envio sem contratar um serviço. O uso será local neste computador; a aplicação ainda não foi publicada e nenhum recurso pago foi provisionado.
- Ainda não temos o endereço Gmail remetente. A conta precisa ter verificação em duas etapas para permitir uma senha de app; o Google informa que essa opção não é recomendada em geral e pode estar indisponível em contas gerenciadas ou com certas proteções. Consulte [Senhas de app do Google](https://support.google.com/accounts/answer/185833?hl=pt-BR).
- Nenhuma senha de app foi criada ou configurada. Não a envie no chat nem a coloque no repositório; ela deve ser configurada somente como variável local protegida.
- A aplicação continua no padrão seguro: backend `console`, allowlist vazia e `COBRANCAS_AGENDAMENTO_ENVIAR=false`. Nenhum e-mail real foi enviado.
- O servidor local de demonstração usa um SQLite temporário, isolado do banco existente, e não tem cobranças de clientes. Para o primeiro teste, cadastrar uma cobrança fictícia para o próprio endereço e executar o comando manualmente; não habilitar cron nem incluir clientes.

**Próxima ação:** informar apenas o endereço remetente Gmail (não a senha), confirmar que a verificação em duas etapas está ativa e criar uma senha de app na página oficial do Google. Depois configurar SMTP localmente e fazer um envio manual para o próprio endereço com allowlist restrita. Sem domínio próprio e sem hospedagem, o app continuará acessível apenas neste computador.

## PostgreSQL

Instale `python -m pip install -e ".[postgres]"` e configure estas variáveis no serviço (não em arquivos versionados):

- `COBRANCAS_DB_ENGINE=postgresql`
- `COBRANCAS_DB_NAME`, `COBRANCAS_DB_USER`, `COBRANCAS_DB_PASSWORD`, `COBRANCAS_DB_HOST`
- `COBRANCAS_DB_PORT` (padrão `5432`)
- `COBRANCAS_DB_SSLMODE=require` quando exigido pelo provedor

SQLite permanece o padrão de desenvolvimento. `COBRANCAS_DB_PATH` pode selecionar outro arquivo SQLite local.

## Django e HTTPS

- `DJANGO_DEBUG=false` (padrão) e `DJANGO_SECRET_KEY` forte, persistente e fornecida pelo gerenciador de segredos do provedor.
- `DJANGO_ALLOWED_HOSTS` deve conter somente os hosts usados pela aplicação.
- Configure `DJANGO_CSRF_TRUSTED_ORIGINS` com origens HTTPS exatas quando necessário.
- O redirecionamento HTTPS fica ativo por padrão fora do modo local. Se o TLS terminar em proxy confiável, configure `DJANGO_TRUST_PROXY_SSL_HEADER=true`; ative somente quando o proxy remover/substituir `X-Forwarded-Proto` recebido externamente. `DJANGO_SECURE_SSL_REDIRECT=false` é opção apenas para ambientes que já impõem HTTPS antes da aplicação.
- Configure HSTS (`DJANGO_SECURE_HSTS_SECONDS`) somente após confirmar HTTPS em todos os hosts; `INCLUDE_SUBDOMAINS` e `PRELOAD` são opções separadas e opt-in.
- Cookies de sessão e CSRF ficam marcados como seguros quando `DEBUG=false`.

## Entrega

O Blueprint seleciona planos pagos (web `0.5c-512mb`, PostgreSQL `0.1c-256mb`; cron segue o plano mínimo da Render) e desliga auto-deploy. Revise os preços vigentes antes de criar os recursos. O Python está fixado em `.python-version`. O serviço web instala `.[postgres]`, coleta arquivos estáticos com WhiteNoise e executa `back/manage.py migrate --noinput` antes de iniciar Gunicorn em `back/`. Após a primeira publicação manual, crie o operador com `python back/manage.py createsuperuser` pelo shell do serviço. Configure domínio e ajuste `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS` se usar domínio próprio.

**Sandbox (captura sem entrega):** o Mailtrap Email Sandbox recebe a mensagem na caixa de teste, mas não entrega na caixa do destinatário. Consulte o [guia oficial de SMTP Sandbox](https://docs.mailtrap.io/email-sandbox/setup/sandbox-smtp-integration.md); o host é `sandbox.smtp.mailtrap.io`, com credenciais próprias do sandbox.

**Entrega real (Email Sending):** requer domínio de envio verificado no Mailtrap. O [guia de SMTP](https://docs.mailtrap.io/email-api-smtp/setup/smtp-integration.md) usa `live.smtp.mailtrap.io`, porta `587` com TLS, usuário `api` e a API token como senha. O remetente deve pertencer ao domínio aprovado. O domínio demo do Mailtrap só pode enviar para o e-mail cadastrado como proprietário da conta; para outros destinatários é necessário verificar seu próprio domínio e concluir a revisão do Mailtrap. Os registros DNS são fornecidos no painel para o domínio escolhido; não os publique sem autorização do proprietário.

Para um primeiro teste **com entrega de verdade**, mantenha `COBRANCAS_EMAIL_DESTINATARIOS_TESTE` limitado ao seu próprio endereço, configure as variáveis SMTP acima no ambiente seguro e use `python back/manage.py processar_cobrancas --data AAAA-MM-DD --enviar` numa data em que exista uma cobrança de teste elegível para esse endereço. Se houver qualquer outra cobrança devida cujo destinatário não esteja na allowlist, o comando recusa o lote inteiro antes de enviar. As credenciais ficam no painel da Render/gerenciador de segredos ou em variáveis locais; nunca no YAML/repositório. No Blueprint, `COBRANCAS_EMAIL_BACKEND` continua `console` por padrão: para live, altere-o deliberadamente para `smtp` no painel e no `render.yaml` antes de sincronizar. O cron mantém `COBRANCAS_AGENDAMENTO_ENVIAR=false` e a rotina segue em simulação até ser habilitada deliberadamente.

O cron está marcado para `0 12 * * 1-5` (Render usa UTC, equivalente a 09:00 em `America/Sao_Paulo`, UTC−3) e chama `processar_cobrancas_agendado`. O comando determina a data pelo timezone Django, ignora sábado/domingo e simula por padrão. Confirme primeiro um envio manual de teste e não inclua endereços de clientes na allowlist sem decisão operacional expressa. Planeje backups restauráveis do PostgreSQL e monitore falhas de aplicação e SMTP.

O workflow `.github/workflows/ci.yml` migra PostgreSQL descartável e roda testes em SQLite isolado. A instância hospedada nunca deve ser usada pelo CI ou pela suíte de testes. Não foi feito deploy nem validação na conta Render; o Blueprint deve ser sincronizado manualmente depois da revisão de custos e dados de domínio.

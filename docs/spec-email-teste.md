# SPEC — Envio de e-mail restrito a destinatários de teste

## Objetivo

Adicionar execução manual da régua com simulação por padrão e envio SMTP real somente quando explicitamente solicitado e somente a endereços autorizados.

## Escopo

- Criar o comando `python back/manage.py processar_cobrancas --data AAAA-MM-DD`; sem `--enviar`, apenas mostra o que seria enviado e não grava histórico nem envia mensagens.
- Com `--enviar`, registrar etapas pendentes idempotentemente e enviar e-mail texto simples para o e-mail cadastrado do cliente.
- Usar allowlist obrigatória por `COBRANCAS_EMAIL_DESTINATARIOS_TESTE` (endereços separados por vírgula, comparação exata sem distinção de maiúsculas/minúsculas). Se estiver ausente/vazia ou qualquer destinatário selecionado não estiver autorizado, abortar antes de enviar qualquer mensagem.
- Configurar SMTP por variáveis de ambiente e manter o backend de console como padrão; envio real deve recusar qualquer backend diferente de SMTP.
- Registrar estados pendente, enviando, enviado e falhou. Marcar `enviando` antes da chamada SMTP. Não repetir automaticamente estados falhos ou enviando; estado enviando após interrupção requer revisão humana.
- Exibir resumo sem e-mails, credenciais ou conteúdo sensível desnecessário. Não enviar etapas para clientes pausados ou cobranças baixadas.

## Plano de execução

1. Ampliar estados do histórico com migração reversível.
2. Adicionar configuração SMTP/allowlist via ambiente, mantendo modo seguro padrão.
3. Criar serviço de envio e comando com `--enviar` explícito, validando todos os destinatários antes do primeiro envio.
4. Testar simulação sem gravação, allowlist ausente/violada, idempotência, estados de sucesso/falha e que nenhum teste abra conexão SMTP real.

## Critérios de aceite

- Sem `--enviar`, nenhuma escrita no banco e nenhuma mensagem enviada.
- Envio real só ocorre com flag explícita, backend SMTP e allowlist não vazia contendo todos os destinatários.
- Falha de validação de destinatário aborta a execução inteira antes de enviar.
- E-mail enviado uma vez não é reenviado em execuções seguintes; falhas/incertezas não são repetidas automaticamente.
- Testes usam backend em memória/mock, sem acesso à rede.

## Riscos

SMTP não oferece garantia geral de entrega exatamente uma vez: uma interrupção após o servidor aceitar a mensagem e antes da confirmação no banco pode deixar o estado enviando. Esse caso não será repetido automaticamente. Credenciais SMTP devem existir somente em variáveis de ambiente e nunca em código, logs ou mensagens de erro.

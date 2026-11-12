# SPEC — Preparação para envio real de e-mail

## Objetivo

Preparar a integração SMTP com Mailtrap Email Sending para entregar uma mensagem real a um endereço controlado pelo operador, preservando bloqueios contra envio acidental a clientes. Esta etapa configura código/documentação, mas não cria conta, grava credenciais, publica serviço nem envia mensagem.

## Escopo

- Trocar as instruções de Email Sandbox pelas instruções de **Email Sending** da Mailtrap.
- Documentar host SMTP `live.smtp.mailtrap.io`, porta `587`, TLS, usuário SMTP `api`, API token como senha, remetente e requisitos de domínio verificado.
- Manter `console` como backend padrão, allowlist vazia por padrão e `COBRANCAS_AGENDAMENTO_ENVIAR=false`.
- Preparar um teste manual com `--enviar` limitado a um endereço controlado pelo operador e coberto pela allowlist; não habilitar destinatários de clientes.
- Manter credenciais no gerenciador de segredos/ambiente, sem incluí-las no repositório ou nas mensagens.
- Não fazer mudança de schema, ativar cron, deploy ou envio real nesta etapa.

## Plano de execução

1. Atualizar documentação de operação para Email Sending e registrar os pré-requisitos do domínio/sender.
2. Revisar configuração existente de SMTP, allowlist, modo seguro padrão e comando manual.
3. Acrescentar testes de configuração/recusa fail-closed se a revisão revelar lacuna; não fazer chamadas SMTP reais nos testes.
4. Validar testes, checks, lint e revisar diff/segredos.

## Critérios de aceite

- A documentação diferencia Sandbox (captura, não entrega) de Email Sending (entrega real) e descreve os valores SMTP atuais.
- Sem segredo, backend SMTP, remetente e destinatário autorizado, nenhum envio é feito.
- O primeiro envio continua sendo uma ação manual explícita; o cron e os envios a clientes permanecem desativados.
- Testes automatizados não contatam serviço externo nem destinatário real.
- Nenhuma credencial é solicitada ou salva no repositório; nenhuma conta/domínio é alterado e nenhum e-mail é enviado durante a implementação.

## Riscos

Uma configuração live pode entregar cobranças reais. A primeira validação deve usar somente o endereço do próprio operador na allowlist. A Mailtrap exige domínio de envio verificado para envio regular; o domínio demo é limitado ao e-mail cadastrado na conta. Registros DNS e informações do domínio dependem do acesso do proprietário e não serão aplicados sem instrução explícita.

## Referências verificadas

- [Mailtrap SMTP integration](https://docs.mailtrap.io/email-api-smtp/setup/smtp-integration.md)
- [Mailtrap sending domains](https://docs.mailtrap.io/email-api-smtp/setup/sending-domain.md)

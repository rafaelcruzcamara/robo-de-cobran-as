# SPEC — Preparação da operação hospedada

## Objetivo

Preparar o MVP para implantação na Render com PostgreSQL gerenciado e rotina de lembretes em dias úteis às 09:00 no fuso `America/Sao_Paulo`, mantendo publicação e envio para clientes reais desativados.

## Escopo

- Acrescentar configuração reproduzível para serviço web e PostgreSQL na Render, variáveis obrigatórias, HTTPS, arquivos estáticos e migrações.
- Preparar um job agendado de segunda a sexta-feira às 09:00 de São Paulo, com data calculada no fuso da aplicação e sem execução em fins de semana.
- Preservar envio bloqueado por padrão e allowlist SMTP de teste; não incluir credenciais nem habilitar destinatários reais.
- Validar páginas e fluxos usando os testes automatizados e HTTP local. Não há validação visual em navegador neste ambiente.
- Não criar recursos na Render, publicar, configurar credenciais externas, enviar e-mails reais nem alterar dados de produção.

## Plano de execução

1. Revisar o comando de processamento, idempotência, configurações de produção e estado do repositório.
2. Implementar configuração de deploy Render e comando agendado com proteção de dias úteis e data no timezone Django.
3. Adicionar testes do job para dias úteis/fins de semana e comportamento de simulação/envio protegido.
4. Documentar provisionamento manual, configuração de segredos no painel, SMTP de teste, validação antes de produção, rollback e passos para publicar somente após decisão do operador.
5. Executar suíte completa, checks Django, verificação de migrações, Ruff e validações HTTP locais; revisar o diff e segurança.

## Critérios de aceite

- A configuração declarativa descreve serviço web e PostgreSQL sem segredo versionado ou publicação automática não aprovada.
- O job executa apenas de segunda a sexta às 09:00 de `America/Sao_Paulo`, calcula a data local correta e é idempotente.
- Sem configuração SMTP/allowlist de teste, o comando recusa envio; a configuração de exemplo não inclui credenciais reais nem endereços de clientes.
- Testes cobrem execução em dia útil, bloqueio em fim de semana e ausência de envio fora de allowlist.
- Páginas principais e CSS respondem localmente; testes web automatizados passam.
- Não há deploy, criação de recursos externos ou envio real nesta tarefa.

## Riscos

Configuração incorreta de cron/timezone pode duplicar ou atrasar lembretes; por isso o job deve calcular a data pelo timezone Django, ser idempotente e verificar dia útil. A ativação de SMTP pode expor dados financeiros; segredos ficam no gerenciador do provedor e o destino permanece limitado à allowlist de teste. Custos, limites de uso e requisitos específicos do provedor devem ser conferidos no painel antes de provisionar recursos.

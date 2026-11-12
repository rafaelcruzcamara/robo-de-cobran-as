# SPEC — Finalização do MVP e polimento

## Objetivo

Fechar lacunas do MVP aprovado, melhorar a experiência visual do painel e deixar o projeto pronto para validação contínua e configuração de PostgreSQL, sem publicar em uma hospedagem nesta etapa.

## Escopo

### Régua configurável

- Manter três etapas fixas: lembrete antes do vencimento, no vencimento e após o vencimento.
- Tornar configuráveis pela web os intervalos em dias corridos; padrões permanecem 2 dias antes, 0 no vencimento e 7 dias depois.
- Validar os intervalos antes de salvar e preservar idempotência/histórico existente ao alterar a configuração.
- A configuração é global para a instalação; sem dias úteis, feriados, etapas extras ou agendamento automático.

### Polimento do front

- Melhorar hierarquia visual, espaçamento, estados de cobrança/cliente, navegação ativa, feedback de formulários e visualização em celular.
- Manter templates e CSS local, acessibilidade básica (rótulos, foco visível, contraste e navegação por teclado) e sem dependência de CDN/biblioteca UI.
- Preservar os fluxos existentes de autenticação, painel, clientes, cobranças, baixa, pausa e importação.

### Preparação operacional

- Permitir configurar SQLite local ou PostgreSQL por variáveis de ambiente; adicionar o driver PostgreSQL como extra opcional `postgres`.
- Criar workflow de CI para instalar dependências e executar testes, Django checks, migrações e Ruff.
- Documentar instalação local, criação de usuário, configuração PostgreSQL, segredos, backups e comandos de operação.
- Não incluir publicação em hospedagem, credenciais reais, envio SMTP real, agendamento automático ou configuração específica de um provedor.

## Plano de execução

1. Adicionar configuração persistente e formulário protegido para os intervalos da régua, com testes de borda e idempotência.
2. Atualizar painel, tabelas, formulários e navegação para melhor hierarquia visual, responsividade e acessibilidade.
3. Adicionar configuração de banco selecionável e extra do driver PostgreSQL; validar migrações em SQLite e PostgreSQL.
4. Adicionar CI e atualizar documentação operacional.
5. Executar a suíte, checks Django, migrações e lint; revisar as páginas e alterações de segurança.

## Critérios de aceite

- Valores padrão da régua continuam 2/0/7 e a configuração salva muda as próximas avaliações sem duplicar etapas já registradas.
- Valores inválidos não alteram a configuração; apenas usuário autenticado pode alterá-la.
- Páginas principais funcionam em largura móvel e desktop, com foco visível, labels e status legíveis.
- SQLite continua sendo o padrão local; as mesmas migrações passam usando PostgreSQL.
- CI executa testes e checks sem segredos; nenhuma credencial real é incluída.
- Envio SMTP real e publicação não são acionados durante os testes.

## Riscos

Alterar intervalos da régua pode mudar quais clientes receberiam lembretes futuros; a configuração é global e mantém histórico por etapa. PostgreSQL exige nova dependência opcional e validação de compatibilidade. A configuração genérica não substitui revisão específica do provedor, TLS, backups e controles de produção antes de tráfego real.

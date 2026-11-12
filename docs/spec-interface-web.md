# SPEC — Interface web do MVP

## Objetivo

Disponibilizar o uso diário do robô em páginas Django renderizadas no servidor, protegidas por autenticação, para acompanhar clientes, cobranças e importações.

## Escopo

- Login/logout com autenticação padrão do Django e validadores de senha; todas as páginas e ações de dados exigem usuário autenticado. Usuários serão provisionados pelo comando `createsuperuser`; sem cadastro público.
- Painel com total em aberto, total vencido e até 10 etapas recentes.
- Listar/cadastrar clientes e cobranças; visualizar detalhes; pausar/retomar cliente; registrar baixa com data informada. Sem exclusão de dados financeiros.
- Importar CSV/XLSX com as regras já implementadas: selecionar arquivo, apresentar erros/duplicatas antes de gravar e persistir tudo em transação somente quando não houver erros. A confirmação exige reenviar o mesmo arquivo; uma assinatura do hash, sem armazenar o conteúdo, impede confirmar uma versão diferente. Uploads de até 5 MB ficam somente em memória e HTML escapa conteúdo importado.
- Reutilizar cliente existente por e-mail normalizado (remover espaços e comparar sem distinção de maiúsculas/minúsculas), com unicidade no banco; preservar pausa e dados do cliente existente.
- Persistir o estado `pago` vindo da importação sem inventar data de baixa; a data fica opcional. Para cliente novo, aplicar `pausado` do arquivo; para cliente já cadastrado, preservar a pausa atual.
- Rejeitar a importação inteira, sem gravar qualquer linha, se uma cobrança já existir com mesmo cliente (e-mail normalizado), descrição (trim/casefold), valor e vencimento; indicar as linhas potencialmente duplicadas. Aplicar unicidade no banco para proteger gravações concorrentes.
- Templates Django e CSS local, sem CDN ou nova dependência externa. Formulários protegidos por CSRF.
- Chave de assinatura gerada aleatoriamente apenas em modo local `DEBUG`; fora dele, exigir `DJANGO_SECRET_KEY` em variável de ambiente.
- Usar o fuso `America/Sao_Paulo` para o limite diário do painel e a data sugerida para baixa.
- Sem configuração de produção/deploy nesta fase.

## Plano de execução

1. Habilitar apps/middleware Django necessários para autenticação, sessões, mensagens, templates e arquivos estáticos locais.
2. Implementar views, URLs, forms e templates para login, painel, clientes, cobranças, baixa e pausa.
3. Integrar upload e revisão de CSV/XLSX a uma gravação transacional.
4. Testar acesso anônimo/autenticado, validação, ações, resumo do painel e rollback de importação inválida.

## Critérios de aceite

- Usuário anônimo é redirecionado ao login; ações POST inválidas não alteram dados.
- A interface não oferece exclusão de clientes/cobranças.
- Pagamento e pausa passam a afetar a régua já existente.
- Importação inválida não grava nenhuma linha; dados apresentados são escapados pelo template.
- As páginas mostram valores em formato monetário local e datas de forma consistente.
- Testes usam banco isolado e dados fictícios.

## Riscos

As páginas expõem dados pessoais e financeiros; autenticação, CSRF, validação de entrada e ausência de exclusão são requisitos. A importação não tem ID externo de cobrança; a detecção por campos pode considerar duplicada uma cobrança legítima idêntica. A política escolhida é rejeitar o arquivo para revisão humana. Uploads devem permanecer em memória e não ser gravados em disco.

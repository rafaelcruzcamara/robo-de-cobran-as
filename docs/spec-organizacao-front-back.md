# SPEC — Organização em pastas `front` e `back`

## Objetivo

Separar visualmente a interface e a aplicação de servidor em pastas de primeiro nível `front/` e `back/`, sem trocar Django, alterar fluxos ou introduzir uma SPA. A reorganização deve manter desenvolvimento, testes e configuração hospedada funcionais.

## Escopo

- Mover templates HTML e arquivos estáticos/CSS para `front/`.
- Mover `manage.py`, projeto Django (`config/`) e aplicação Python (`src/cobrancas/`) para `back/`.
- Manter na raiz os arquivos de projeto e operação que coordenam as duas partes: `pyproject.toml`, `render.yaml`, README, documentação, CI e testes.
- Atualizar caminhos de templates/static, descoberta do pacote, imports/testes, comandos locais, CI e comandos Render.
- Preservar todas as rotas, autenticação, visual/funcionalidade do painel, dados e dependências existentes.
- Não migrar para React/Vue, não mudar API/banco/schema e não realizar deploy.

## Plano de execução

1. Parar o servidor local temporário iniciado para demonstração.
2. Criar `front/templates/` e `front/static/`; mover os assets atuais mantendo os subdiretórios e nomes.
3. Criar `back/`; mover `manage.py`, `config/` e `src/` para lá e atualizar `BASE_DIR`, configuração de templates/static e descoberta do pacote.
4. Ajustar CI, `render.yaml`, documentação e comandos de desenvolvimento para usar `back/manage.py` e o layout novo.
5. Executar a suíte completa, checks Django, coleta de estáticos, validação HTTP da página/CSS, migrações e Ruff; revisar referências antigas e o diff.

## Critérios de aceite

- A estrutura tem `front/` e `back/` claros, mantendo os assets visuais fora da aplicação backend.
- Login, painel, clientes, cobranças, importação e régua mantêm comportamento e rotas atuais.
- `python -m pytest`, Django checks, migrações e Ruff passam a partir da raiz.
- `collectstatic` encontra os assets em `front/static/`; a página servida inclui CSS funcional.
- Comandos de CI e Render apontam para os caminhos novos e o pacote Python continua instalável.
- Nenhuma migração de banco, perda de dados, troca de stack ou deploy ocorre como parte da reorganização.

## Riscos

Alterar caminhos pode quebrar imports, testes, localização de templates/estáticos ou comandos de hospedagem. O servidor de demonstração atual usa o layout antigo e será interrompido para a mudança; será necessário iniciá-lo novamente após a validação. O banco temporário de demonstração e o banco atual não devem ser movidos nem modificados.

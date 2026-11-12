# SPEC — Persistência de cobranças e histórico idempotente

## Objetivo

Persistir clientes, cobranças e etapas de cobrança previstas em SQLite usando Django ORM, com garantia no banco de que reprocessar uma etapa não cria registros duplicados.

## Escopo

- Adicionar Django como dependência e configurar um projeto mínimo, sem telas ou envio de e-mail nesta fase.
- Modelar cliente (nome, e-mail e pausa), cobrança (descrição, valor decimal, vencimento e baixa) e histórico de etapa (cobrança, etapa, data e estado pendente).
- Garantir unicidade de cobrança + etapa no banco; criar etapas pendentes dentro de transação.
- Usar SQLite no desenvolvimento e manter configuração compatível com a decisão registrada de PostgreSQL como alvo futuro, sem configurar produção agora.
- Manter a simulação CLI atual sem efeitos colaterais; a persistência será uma operação separada.

## Plano de execução

1. Confirmar e adicionar a dependência Django aprovada.
2. Configurar a aplicação e modelos, gerando migração inicial.
3. Implementar operação transacional para registrar etapas pendentes somente para cobranças não pagas e clientes não pausados.
4. Testar migração, unicidade/idempotência, pausa, baixa e rollback/atomicidade.

## Critérios de aceite

- Banco SQLite pode ser criado/migrado localmente.
- Duas execuções para a mesma cobrança e etapa deixam um único histórico.
- Etapa não é registrada para cobrança paga ou cliente pausado.
- Valores são armazenados com precisão decimal.
- Testes usam banco isolado e não dependem de dados reais.
- Nenhum e-mail, integração de rede ou interface web é iniciado nesta fase.

## Riscos

Os modelos conterão dados pessoais e financeiros; a configuração local deve evitar credenciais no código, e os testes devem usar dados fictícios. O formato de importação atual não terá persistência automática até uma fase de integração explícita. A restrição de unicidade precisa ser aplicada pelo banco para permanecer segura sob execuções concorrentes.

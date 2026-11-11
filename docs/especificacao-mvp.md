# Especificação — MVP do robô de cobrança

## Objetivo

Reduzir o trabalho manual de acompanhamento de contas a receber, com lembretes respeitosos e registro verificável das ações.

## Escopo

Inclui aplicação Django com páginas renderizadas no servidor, importação CSV e Excel, cadastro, motor de regras puro, execução manual e simulada, histórico idempotente, baixa de pagamento, pausa de cliente, painel e envio de e-mail limitado a endereços de teste autorizados. SQLite será usado no desenvolvimento; PostgreSQL é o alvo de produção. Dados de desenvolvimento serão fictícios.

Ficam fora do MVP: WhatsApp, processamento de pagamentos, negociação de descontos e agendamento diário automatizado.

## Plano de execução

1. Preparar ambiente, Git e ferramentas de qualidade.
2. Implementar e testar o motor puro de regras.
3. Importar e validar arquivos CSV/Excel.
4. Criar o robô de linha de comando e simulação.
5. Persistir dados e garantir idempotência no banco.
6. Integrar envio de e-mail e tratamento de falhas.
7. Construir as telas web e o painel.
8. Preparar operação, CI e entrega.

## Critérios de aceite

- Motor de regras recebe a data como parâmetro e não acessa banco, relógio ou rede.
- Repetir a execução não duplica uma etapa de cobrança.
- Pagamentos baixados e clientes pausados não recebem cobranças.
- Simulação não envia e-mail.
- Testes automatizados cobrem regras e idempotência.
- E-mails do MVP só podem ser enviados a destinatários de teste autorizados.

## Riscos

O envio de e-mails envolve privacidade e pode contatar destinatários incorretos se a restrição de teste falhar. Dados financeiros e pessoais exigem minimização, proteção, descadastro e validação profissional das obrigações legais antes de uso real. Datas, fuso, dias úteis, feriados, agrupamento e política de mensagens precisam de decisões explícitas antes das fases correspondentes.

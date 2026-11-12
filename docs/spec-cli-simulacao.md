# SPEC — Comando CLI de simulação

## Objetivo

Permitir executar manualmente a régua sobre um arquivo importado e conferir quais lembretes seriam gerados em uma data informada.

## Escopo

Adicionar `python -m cobrancas simular <arquivo> --data AAAA-MM-DD`. O comando aceita CSV e XLSX já suportados, avalia cada registro usando o motor de regras e imprime um resumo com os lembretes previstos, identificando cliente, descrição, valor e etapa. Erros de importação são reportados por linha/campo; nenhum arquivo é alterado.

O comando é sempre simulado: não envia e-mail, não acessa rede, banco ou relógio do sistema e não persiste dados. A data é obrigatória. E-mails não são exibidos.

## Plano de execução

1. Adicionar ponto de entrada `python -m cobrancas` com argumentos validados.
2. Ler extensão CSV/XLSX e delegar a importação às funções existentes.
3. Avaliar as cobranças válidas para a data informada e apresentar o resultado.
4. Cobrir sucesso, ausência de lembretes, formato/data inválidos e erros de registros.

## Critérios de aceite

- Execução reproduzível para uma mesma entrada e data.
- Sem `--data`, data inválida, extensão não suportada ou importação inválida, o comando retorna código de erro apropriado.
- Cobranças pagas/pausadas são omitidas conforme as regras existentes.
- Simulação nunca envia mensagens nem expõe e-mails.

## Riscos

Valores e nomes impressos podem ser dados financeiros/pessoais; a saída deve conter somente os campos necessários e não deve registrar conteúdo de arquivo em logs. O CLI continua limitado a simulação enquanto não houver persistência ou integração de envio aprovada.

# SPEC — Importação de cobranças CSV e Excel

## Objetivo

Ler arquivos de cobranças e validar seus registros antes de qualquer persistência, informando erros de forma localizada por linha e coluna.

## Escopo

Aceitar CSV UTF-8 delimitado por ponto e vírgula e planilhas Excel XLSX. O CSV usa valor decimal com vírgula (por exemplo, `1234,56`) e data `DD/MM/AAAA`. Em XLSX, aceitar valores numéricos e células de data nativas do Excel. Ambos usam as colunas `cliente`, `email`, `descricao`, `valor`, `vencimento`, `pago` e `pausado`. O leitor não persiste dados, não envia mensagens e não usa rede.

## Plano de execução

1. Implementar leitura isolada de CSV e XLSX em estruturas validadas.
2. Validar cabeçalhos, campos obrigatórios, e-mail, valor monetário, data e flags de estado.
3. Retornar registros válidos e erros com número de linha/campo, sem descartar silenciosamente linhas inválidas.
4. Testar formatos válidos, arquivos malformados e entradas inválidas.

## Critérios de aceite

- Os dois formatos aceitam as mesmas colunas e regras de validação.
- Valores monetários são tratados como decimal, sem arredondamento binário de `float`; o CSV usa vírgula decimal.
- Datas CSV são `DD/MM/AAAA`; XLSX pode fornecer célula nativa de data. Erros identificam linha e campo.
- A importação não persiste nem envia dados.
- Arquivo vazio, cabeçalho ausente/duplicado e tipos inesperados são reportados com segurança.

## Riscos

Os arquivos podem conter dados pessoais e financeiros; devem ser processados sem logs de conteúdo e sem persistência nesta etapa. O suporte XLSX requer a dependência externa `openpyxl`. Arquivos com formatos diferentes dos definidos devem gerar erros de validação, não conversões presumidas.

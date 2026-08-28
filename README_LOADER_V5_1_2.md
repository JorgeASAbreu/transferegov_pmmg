# Loader V5.1.2 — correção de integridade

Esta versão corrige dois problemas encontrados na primeira carga real:

1. `dim_executor`: a combinação CNPJ + agência + conta não é única no Transferegov.
   O mesmo executor jurídico/conta pode receber diferentes `id_executor` de origem.
   A chave primária continua sendo `id_executor`; o índice bancário passa a ser não único.

2. Auditoria: a finalização de erro não usa mais um parâmetro sem tipo em `%s IS NULL`,
   eliminando `psycopg.errors.IndeterminateDatatype`.

## Aplicação

Mescle/substitua os arquivos deste pacote na raiz do projeto e execute:

```powershell
python -m unittest tests.test_loader_v5_1 tests.test_correcao_v5_1_2 -v
python migrar_v5_1_2.py
python carregar_postgresql_v5_1.py --esperado-tes 90
```

Não é necessário apagar banco nem tabelas. A carga principal que falhou estava em uma
transação e é revertida pelo context manager do psycopg; a linha de auditoria iniciada
separadamente pode ter ficado `EM_EXECUCAO` e será tratada na validação pós-carga.

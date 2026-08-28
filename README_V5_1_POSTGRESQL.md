# V5.1 — PostgreSQL inicial

Este pacote cria o primeiro schema analítico persistente do projeto.

## Objetivo desta etapa

Persistir, sem perda conceitual:

- Transferência federal;
- Transferência operacional para a conta executor;
- Movimentações adicionais ainda não classificadas;
- Saldos BB no nível correto da conta;
- Atribuição (ou não atribuição) do saldo BB a cada TE;
- Movimentações de gestão financeira;
- Campos futuros de SIAFI/MG, inicialmente NULL.

## Convenção monetária

Todos os valores monetários analíticos são `BIGINT` em centavos.

`1 = R$ 0,01`
`100 = R$ 1,00`

Percentuais usam `NUMERIC`, nunca `FLOAT`.

## Instalação

No ambiente virtual:

```powershell
pip install "psycopg[binary]>=3.2,<4"
```

## Variáveis de ambiente

Não grave credenciais no código.

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="transferegov_pmmg"
$env:PGUSER="postgres"
$env:PGPASSWORD="SUA_SENHA"
```

## Criar o banco vazio

O database deve existir antes do schema. Exemplo via psql:

```sql
CREATE DATABASE transferegov_pmmg;
```

Depois, na raiz do projeto:

```powershell
$env:PYTHONPATH="$PWD\src"
python init_db.py
```

## Teste estrutural

```powershell
python -m unittest tests.test_schema_v5_1 -v
```

## Próximo passo

Depois que o schema for validado no PostgreSQL:

1. implementar os loaders/upserts;
2. carregar Transferegov;
3. carregar BB;
4. validar contagens e valores;
5. integrar SIAFI/MG;
6. criar views para Power BI.

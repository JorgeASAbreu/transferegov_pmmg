# Loader V5.1 — Transferegov + BB → PostgreSQL

Este pacote **agrega** arquivos ao projeto; não substitui o schema já criado.

Arquivos novos:
- `carregar_postgresql_v5_1.py`
- `src/transferegov/persistencia/loader_v5_1.py`
- `tests/test_loader_v5_1.py`

## Garantias da carga

- UPSERT/idempotência nas dimensões e fatos.
- Transação única para dados; rollback em erro.
- Auditoria persistente em `transferegov.etl_carga`, inclusive para falhas.
- Valores monetários analíticos em centavos inteiros.
- `None` permanece `NULL`.
- Valor federal e operacional permanecem lado a lado.
- Movimentações adicionais permanecem não classificadas; não são tratadas como rendimento.
- Snapshot BB é armazenado no nível da conta.
- Conta compartilhada nunca replica o saldo total para cada TE.
- SHA-256 dos arquivos-fonte é registrado na auditoria.

## Teste antes da carga

```powershell
python -m unittest tests.test_loader_v5_1 -v
```

## Carga atual de referência (90 TEs)

Com as variáveis `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` e `PYTHONPATH` definidas:

```powershell
python carregar_postgresql_v5_1.py --esperado-tes 90
```

O BB será carregado se existir `dados/bb/saldos_investimentos.json`.
Se quiser carregar apenas Transferegov:

```powershell
python carregar_postgresql_v5_1.py --esperado-tes 90 --sem-bb
```

A carga pode ser reexecutada. UPSERT evita duplicação das entidades atuais; snapshots BB são únicos por conta + instante de consulta.

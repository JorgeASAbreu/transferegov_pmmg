BEGIN;

-- V5.1.2
-- O id_executor é a chave de origem. Uma mesma pessoa jurídica e a mesma
-- conta bancária podem aparecer em vários registros com id_executor distintos.
-- Logo (cnpj, agencia, conta) não é chave candidata e não pode ser UNIQUE.

DROP INDEX IF EXISTS transferegov.ux_dim_executor_cnpj_conta;

CREATE INDEX IF NOT EXISTS ix_dim_executor_cnpj_conta
ON transferegov.dim_executor (
    cnpj_executor,
    numero_agencia_executor,
    numero_conta_executor
)
WHERE cnpj_executor IS NOT NULL
  AND numero_agencia_executor IS NOT NULL
  AND numero_conta_executor IS NOT NULL;

COMMIT;

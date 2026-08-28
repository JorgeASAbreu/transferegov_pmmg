from __future__ import annotations

from pathlib import Path

from transferegov.persistencia.db import conexao


ARQUIVO_SCHEMA = Path("sql/schema_v5_1.sql")


def main() -> None:
    if not ARQUIVO_SCHEMA.exists():
        raise FileNotFoundError(
            f"Schema SQL não encontrado: {ARQUIVO_SCHEMA}"
        )

    sql = ARQUIVO_SCHEMA.read_text(
        encoding="utf-8"
    )

    with conexao() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)

    print(
        "Schema PostgreSQL 'transferegov' criado/validado com sucesso."
    )


if __name__ == "__main__":
    main()

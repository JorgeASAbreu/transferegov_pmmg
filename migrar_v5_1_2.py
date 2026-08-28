from pathlib import Path

from transferegov.persistencia.db import conexao


def main() -> None:
    caminho = Path("sql/migrations/v5_1_2_corrige_dim_executor.sql")
    sql = caminho.read_text(encoding="utf-8")

    with conexao() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)

    print("Migração V5.1.2 aplicada com sucesso.")


if __name__ == "__main__":
    main()

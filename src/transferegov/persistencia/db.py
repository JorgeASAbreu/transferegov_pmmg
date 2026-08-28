from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg import Connection


def _obrigatoria(nome: str) -> str:
    valor = os.getenv(nome)
    if not valor:
        raise RuntimeError(
            f"Variável de ambiente obrigatória não definida: {nome}"
        )
    return valor


def dsn_postgres() -> str:
    """
    Monta a conexão exclusivamente por variáveis de ambiente.

    Nenhuma credencial deve ser gravada no código-fonte.
    """
    host = _obrigatoria("PGHOST")
    database = _obrigatoria("PGDATABASE")
    user = _obrigatoria("PGUSER")
    password = _obrigatoria("PGPASSWORD")
    port = os.getenv("PGPORT", "5432")

    return (
        f"host={host} "
        f"port={port} "
        f"dbname={database} "
        f"user={user} "
        f"password={password}"
    )


@contextmanager
def conexao() -> Iterator[Connection]:
    """
    Abre uma conexão transacional.

    Em sucesso, commit.
    Em exceção, rollback automático pelo context manager do psycopg.
    """
    with psycopg.connect(dsn_postgres()) as conn:
        yield conn

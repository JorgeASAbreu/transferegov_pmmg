from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path


NOME_LOGGER_RAIZ = "transferegov"


def configurar_logger(
    nome: str = NOME_LOGGER_RAIZ,
) -> logging.Logger:
    """
    Configura e retorna um logger do projeto.

    Os logs são enviados simultaneamente para:
    - terminal;
    - arquivo diário dentro de ./logs.
    """

    logger_raiz = logging.getLogger(
        NOME_LOGGER_RAIZ
    )

    if not logger_raiz.handlers:
        logger_raiz.setLevel(logging.INFO)

        pasta_logs = Path("logs")
        pasta_logs.mkdir(
            parents=True,
            exist_ok=True,
        )

        data_atual = datetime.now().strftime(
            "%Y-%m-%d"
        )

        arquivo_log = (
            pasta_logs
            / f"transferegov_{data_atual}.log"
        )

        formato = logging.Formatter(
            (
                "%(asctime)s | "
                "%(levelname)s | "
                "%(name)s | "
                "%(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        arquivo_handler = logging.FileHandler(
            arquivo_log,
            encoding="utf-8",
        )

        arquivo_handler.setLevel(
            logging.INFO
        )

        arquivo_handler.setFormatter(
            formato
        )

        console_handler = logging.StreamHandler()

        console_handler.setLevel(
            logging.INFO
        )

        console_handler.setFormatter(
            formato
        )

        logger_raiz.addHandler(
            arquivo_handler
        )

        logger_raiz.addHandler(
            console_handler
        )

        logger_raiz.propagate = False

    return logging.getLogger(nome)
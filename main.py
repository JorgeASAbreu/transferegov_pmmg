from __future__ import annotations

import json
from pathlib import Path

from transferegov.extrator import ExtratorPMMG
from transferegov.logger import configurar_logger


logger = configurar_logger(
    "transferegov.main"
)


def salvar_json(
    dados: list[dict],
    caminho: str,
) -> None:
    arquivo = Path(caminho)

    arquivo.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with arquivo.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            dados,
            f,
            ensure_ascii=False,
            indent=2,
        )


def main() -> None:
    logger.info(
        "=" * 60
    )

    logger.info(
        "TRANSFEREGOV - EXTRAÇÃO PMMG"
    )

    logger.info(
        "=" * 60
    )

    try:
        extrator = ExtratorPMMG()

        dados = extrator.extrair()

        caminho_saida = (
            "dados/transferegov_pmmg.json"
        )

        salvar_json(
            dados,
            caminho_saida,
        )

        total = len(dados)

        total_ok = sum(
            1
            for registro in dados
            if registro.get(
                "status_extracao"
            ) == "OK"
        )

        total_com_erros = sum(
            1
            for registro in dados
            if registro.get(
                "status_extracao"
            ) == "COM_ERROS"
        )

        logger.info(
            "=" * 60
        )

        logger.info(
            "EXTRAÇÃO CONCLUÍDA"
        )

        logger.info(
            "Registros processados=%s",
            total,
        )

        logger.info(
            "Registros OK=%s",
            total_ok,
        )

        logger.info(
            "Registros COM_ERROS=%s",
            total_com_erros,
        )

        logger.info(
            "Arquivo gerado=%s",
            caminho_saida,
        )

        logger.info(
            "=" * 60
        )

    except Exception:
        logger.exception(
            "Falha crítica durante a extração"
        )

        raise


if __name__ == "__main__":
    main()
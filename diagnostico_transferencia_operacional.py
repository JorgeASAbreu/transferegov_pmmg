from __future__ import annotations

from collections import Counter
from pathlib import Path

from transferegov.transformacao.moeda import formatar_reais
from transferegov.transformacao.transformador import (
    TransformadorTransferegov,
)
from transferegov.transformacao.transferencia_operacional import (
    TransferenciaOperacionalExecutor,
)


ARQUIVO = Path("dados/transferegov_pmmg.json")


def main() -> None:
    tabelas = TransformadorTransferegov(
        str(ARQUIVO)
    ).normalizar()

    analises = TransferenciaOperacionalExecutor(
        tabelas
    ).analisar()

    por_status = Counter(
        item["status_transferencia_operacional"]
        for item in analises
    )

    com_adicionais = [
        item
        for item in analises
        if item.get(
            "tem_movimentacao_adicional_executor"
        )
    ]

    print("=" * 100)
    print(
        "DIAGNÓSTICO — TRANSFERÊNCIA OPERACIONAL "
        "PARA CONTA EXECUTOR"
    )
    print("=" * 100)

    for item in analises:
        print(
            f"id_plano={item['id_plano_acao']} | "
            f"executor={item['id_agencia_conta_executor']} | "
            f"status={item['status_transferencia_operacional']} | "
            f"previsto="
            f"{formatar_reais(item['valor_previsto_executor_centavos'])} | "
            f"principal="
            f"{formatar_reais(item['valor_transferido_operacional_centavos'])} | "
            f"adicional="
            f"{formatar_reais(item['valor_movimentacoes_adicionais_executor_centavos'])}"
        )

    print()
    print("=" * 100)
    print("RESUMO")
    print("=" * 100)
    print(f"Total de executores/TEs analisados: {len(analises)}")

    for status, quantidade in sorted(
        por_status.items()
    ):
        print(f"{status}: {quantidade}")

    print(
        "TEs com movimentação adicional ainda "
        f"não classificada: {len(com_adicionais)}"
    )

    if len(analises) != 90:
        raise AssertionError(
            f"Base de referência esperava 90 registros; "
            f"foram encontrados {len(analises)}."
        )

    # Caso de referência: 09032025-079703 / id 79703.
    caso = next(
        (
            item
            for item in analises
            if item["id_plano_acao"] == 79703
        ),
        None,
    )

    if caso is not None:
        print()
        print("CASO DE REFERÊNCIA — id_plano_acao=79703")
        print(
            "principal: "
            + str(
                formatar_reais(
                    caso[
                        "valor_transferido_operacional_centavos"
                    ]
                )
            )
        )
        print(
            "movimentação adicional: "
            + str(
                formatar_reais(
                    caso[
                        "valor_movimentacoes_adicionais_executor_centavos"
                    ]
                )
            )
        )

    print()
    print(
        "OBSERVAÇÃO: movimentações adicionais NÃO foram "
        "classificadas como rendimento."
    )


if __name__ == "__main__":
    main()

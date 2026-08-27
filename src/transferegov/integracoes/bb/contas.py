from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


class DescobridorContasBB:
    """
    Descobre automaticamente as contas bancárias
    associadas às Transferências Especiais a partir
    do JSON produzido pela V4.

    Granularidade do arquivo de saída:
        1 registro = 1 agência/conta única.

    Uma mesma conta pode estar associada a vários
    Planos de Ação, especialmente antes de 2025.
    """

    ANO_INICIO_CONTA_EXCLUSIVA = 2025

    def __init__(
        self,
        caminho_origem: str = "dados/transferegov_pmmg.json",
        caminho_destino: str = "dados/bb/contas.json",
    ) -> None:
        self.caminho_origem = Path(
            caminho_origem
        )

        self.caminho_destino = Path(
            caminho_destino
        )

    # ==================================================
    # CARGA
    # ==================================================

    def carregar_dados(
        self,
    ) -> list[dict[str, Any]]:
        if not self.caminho_origem.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: "
                f"{self.caminho_origem}"
            )

        with self.caminho_origem.open(
            "r",
            encoding="utf-8",
        ) as arquivo:
            dados = json.load(arquivo)

        if not isinstance(dados, list):
            raise ValueError(
                "O JSON principal deve conter "
                "uma lista de registros."
            )

        return dados

    # ==================================================
    # DESCOBERTA
    # ==================================================

    def descobrir(
        self,
    ) -> list[dict[str, Any]]:
        dados = self.carregar_dados()

        contas: dict[
            str,
            dict[str, Any],
        ] = {}

        planos_por_conta: dict[
            str,
            list[dict[str, Any]],
        ] = defaultdict(list)

        for registro in dados:
            plano = (
                registro.get("plano_acao")
                or {}
            )

            id_agencia_conta = plano.get(
                "id_agencia_conta"
            )

            if not id_agencia_conta:
                continue

            agencia, conta = (
                self._separar_agencia_conta(
                    id_agencia_conta
                )
            )

            if (
                agencia is None
                or conta is None
            ):
                continue

            id_plano_acao = plano.get(
                "id_plano_acao"
            )

            ano_plano_acao = plano.get(
                "ano_plano_acao"
            )

            planos_por_conta[
                id_agencia_conta
            ].append(
                {
                    "id_plano_acao": (
                        id_plano_acao
                    ),
                    "codigo_plano_acao": (
                        plano.get(
                            "codigo_plano_acao"
                        )
                    ),
                    "ano_plano_acao": (
                        ano_plano_acao
                    ),
                }
            )

            if (
                id_agencia_conta
                not in contas
            ):
                contas[
                    id_agencia_conta
                ] = {
                    "id_agencia_conta": (
                        id_agencia_conta
                    ),
                    "agencia": agencia,
                    "conta": conta,
                    "ativa": True,
                }

        resultado: list[
            dict[str, Any]
        ] = []

        for (
            id_agencia_conta,
            conta_base,
        ) in contas.items():
            planos = planos_por_conta[
                id_agencia_conta
            ]

            anos = sorted(
                {
                    plano.get(
                        "ano_plano_acao"
                    )
                    for plano in planos
                    if plano.get(
                        "ano_plano_acao"
                    )
                    is not None
                }
            )

            conta_compartilhada = (
                self._eh_conta_compartilhada(
                    planos
                )
            )

            registro_conta = {
                **conta_base,

                "quantidade_planos_acao": (
                    len(planos)
                ),

                "planos_acao": planos,

                "anos_planos_acao": anos,

                "conta_compartilhada": (
                    conta_compartilhada
                ),

                "conta_exclusiva_te": (
                    not conta_compartilhada
                ),
            }

            resultado.append(
                registro_conta
            )

        resultado.sort(
            key=lambda item: (
                item["agencia"],
                item["conta"],
            )
        )

        return resultado

    # ==================================================
    # REGRA DE CONTA
    # ==================================================

    def _eh_conta_compartilhada(
        self,
        planos: list[dict[str, Any]],
    ) -> bool:
        """
        Regra adotada no projeto:

        - até 2024 uma conta pode atender mais
          de uma TE;
        - a partir de 2025, 1 TE = 1 conta.

        Também considera o vínculo real:
        se houver mais de um Plano de Ação
        associado à mesma conta, ela é marcada
        como compartilhada.
        """

        if len(planos) > 1:
            return True

        anos = [
            plano.get(
                "ano_plano_acao"
            )
            for plano in planos
            if plano.get(
                "ano_plano_acao"
            )
            is not None
        ]

        if not anos:
            return False

        return any(
            ano
            < self.ANO_INICIO_CONTA_EXCLUSIVA
            for ano in anos
        )

    # ==================================================
    # PARSE AGÊNCIA / CONTA
    # ==================================================

    @staticmethod
    def _separar_agencia_conta(
        id_agencia_conta: str,
    ) -> tuple[str | None, str | None]:
        """
        Espera o padrão:

            AGENCIA-CONTA

        Exemplo:

            1615-27418
        """

        valor = str(
            id_agencia_conta
        ).strip()

        if "-" not in valor:
            return None, None

        agencia, conta = valor.split(
            "-",
            1,
        )

        agencia = agencia.strip()
        conta = conta.strip()

        if not agencia or not conta:
            return None, None

        return agencia, conta

    # ==================================================
    # SALVAMENTO
    # ==================================================

    def salvar(
        self,
        contas: list[dict[str, Any]],
    ) -> None:
        self.caminho_destino.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.caminho_destino.open(
            "w",
            encoding="utf-8",
        ) as arquivo:
            json.dump(
                contas,
                arquivo,
                ensure_ascii=False,
                indent=2,
            )

    def executar(
        self,
    ) -> list[dict[str, Any]]:
        contas = self.descobrir()

        self.salvar(
            contas
        )

        return contas
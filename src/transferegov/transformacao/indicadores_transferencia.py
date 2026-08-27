from __future__ import annotations

from collections import defaultdict
from typing import Any


class IndicadoresTransferencia:
    def __init__(
        self,
        transferencias: list[dict[str, Any]],
    ) -> None:
        self.transferencias = transferencias

    def resumo_por_ano(
        self,
    ) -> list[dict[str, Any]]:
        """
        Responde:
        - Quantas TEs existem por ano?
        - Quanto foi destinado por ano?
        - Quanto foi transferido por ano?
        - Qual o saldo das TEs com conta exclusiva?
        - Quantas TEs possuem conta compartilhada?
        """

        dados: dict[int, dict[str, Any]] = {}

        for te in self.transferencias:
            ano = te.get("ano_plano_acao")

            if ano is None:
                continue

            if ano not in dados:
                dados[ano] = {
                    "ano": ano,
                    "quantidade_te": 0,
                    "valor_destinado": 0.0,
                    "valor_transferido": 0.0,

                    "saldo_te_exclusivas": 0.0,

                    "quantidade_te_saldo_confiavel": 0,
                    "quantidade_te_conta_compartilhada": 0,
                }

            linha = dados[ano]

            linha["quantidade_te"] += 1

            linha["valor_destinado"] += (
                te.get("valor_destinado") or 0
            )

            linha["valor_transferido"] += (
                te.get("valor_transferido") or 0
            )

            if te.get("saldo_conta_te_confiavel") is True:
                saldo = te.get("saldo_conta")

                if saldo is not None:
                    linha["saldo_te_exclusivas"] += saldo

                    linha[
                        "quantidade_te_saldo_confiavel"
                    ] += 1

            if te.get("conta_compartilhada") is True:
                linha[
                    "quantidade_te_conta_compartilhada"
                ] += 1

        return [
            dados[ano]
            for ano in sorted(dados)
        ]

    def ranking_parlamentares(
        self,
    ) -> list[dict[str, Any]]:
        """
        Ranking de parlamentares por:
        - valor destinado;
        - quantidade de TEs;
        - valor transferido.
        """

        dados = defaultdict(
            lambda: {
                "quantidade_te": 0,
                "valor_destinado": 0.0,
                "valor_transferido": 0.0,
            }
        )

        for te in self.transferencias:
            parlamentar = (
                te.get("nome_parlamentar")
                or "NÃO INFORMADO"
            )

            dados[
                parlamentar
            ]["quantidade_te"] += 1

            dados[
                parlamentar
            ]["valor_destinado"] += (
                te.get("valor_destinado") or 0
            )

            dados[
                parlamentar
            ]["valor_transferido"] += (
                te.get("valor_transferido") or 0
            )

        resultado = []

        for parlamentar, valores in dados.items():
            resultado.append(
                {
                    "parlamentar": parlamentar,
                    **valores,
                }
            )

        return sorted(
            resultado,
            key=lambda linha: (
                linha["valor_destinado"]
            ),
            reverse=True,
        )

    def resumo_planos_trabalho(
        self,
    ) -> dict[str, int]:
        """
        Responde inicialmente:
        - quantas TEs possuem PT aprovado;
        - quantas passaram por complementação;
        - quantas possuem relatório de gestão.
        """

        return {
            "te_com_plano_aprovado": sum(
                1
                for te in self.transferencias
                if (
                    te.get(
                        "quantidade_planos_aprovados"
                    )
                    or 0
                )
                > 0
            ),

            "te_com_complementacao": sum(
                1
                for te in self.transferencias
                if te.get(
                    "teve_complementacao"
                )
                is True
            ),

            "te_com_relatorio_gestao": sum(
                1
                for te in self.transferencias
                if te.get(
                    "tem_relatorio_gestao"
                )
                is True
            ),

            "te_sem_relatorio_gestao": sum(
                1
                for te in self.transferencias
                if not te.get(
                    "tem_relatorio_gestao"
                )
            ),

            "te_multiplos_orgaos_analise": sum(
                1
                for te in self.transferencias
                if te.get(
                    "multiplos_orgaos_analisadores"
                )
                is True
            ),
        }
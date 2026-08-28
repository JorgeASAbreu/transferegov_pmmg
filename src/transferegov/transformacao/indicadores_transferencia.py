from __future__ import annotations

from collections import defaultdict
from typing import Any


class IndicadoresTransferencia:
    """
    Gera indicadores e resumos a partir da tabela analítica
    f_transferencia.

    CONVENÇÃO MONETÁRIA OBRIGATÓRIA
    --------------------------------
    Todos os valores monetários recebidos desta camada devem estar
    expressos em CENTAVOS INTEIROS e usar o sufixo "_centavos".

    Exemplos:
        1          = R$ 0,01
        100        = R$ 1,00
        123_456    = R$ 1.234,56
        52_735_000 = R$ 527.350,00

    Regras para manutenção:
        - NÃO usar float em agregações monetárias.
        - NÃO converter centavos para reais nesta camada.
        - NÃO renomear campos monetários removendo "_centavos".
        - A conversão para reais pertence à camada de apresentação.
        - None significa ausência de informação.
        - Valores conhecidos iguais a zero devem permanecer 0.

    IMPORTANTE
    ----------
    Esta classe não é responsável por converter valores brutos
    provenientes de APIs ou sistemas externos. Ela recebe uma base
    analítica que já passou pelas camadas de transformação e
    consolidação financeira.
    """

    def __init__(
        self,
        transferencias: list[dict[str, Any]],
    ) -> None:
        self.transferencias = transferencias

    def resumo_por_ano(
        self,
    ) -> list[dict[str, Any]]:
        """
        Produz resumo anual das Transferências Especiais.

        Responde:
        - Quantas TEs existem por ano?
        - Quanto foi destinado por ano?
        - Quanto foi transferido por ano?
        - Qual o saldo das TEs com conta exclusiva/confiável?
        - Quantas TEs possuem conta compartilhada?

        Todos os campos monetários retornados estão em centavos.
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

                    # Valores monetários em centavos inteiros.
                    "valor_destinado_centavos": 0,
                    "valor_transferido_centavos": 0,
                    "saldo_te_exclusivas_centavos": 0,

                    "quantidade_te_saldo_confiavel": 0,
                    "quantidade_te_conta_compartilhada": 0,
                }

            linha = dados[ano]

            linha["quantidade_te"] += 1

            valor_destinado_centavos = te.get(
                "valor_destinado_centavos"
            )

            if valor_destinado_centavos is not None:
                linha[
                    "valor_destinado_centavos"
                ] += valor_destinado_centavos

            valor_transferido_centavos = te.get(
                "valor_transferido_centavos"
            )

            if valor_transferido_centavos is not None:
                linha[
                    "valor_transferido_centavos"
                ] += valor_transferido_centavos

            # O saldo só entra no agregado anual quando a própria
            # f_transferencia considera que ele é confiável para a TE.
            if te.get("saldo_conta_te_confiavel") is True:
                saldo_conta_centavos = te.get(
                    "saldo_conta_centavos"
                )

                if saldo_conta_centavos is not None:
                    linha[
                        "saldo_te_exclusivas_centavos"
                    ] += saldo_conta_centavos

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
        Gera ranking de parlamentares por:
        - valor destinado;
        - quantidade de TEs;
        - valor transferido.

        Ordenação:
            maior valor destinado primeiro.

        Todos os valores monetários retornados estão em centavos.
        """
        dados: defaultdict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "quantidade_te": 0,
                "valor_destinado_centavos": 0,
                "valor_transferido_centavos": 0,
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

            valor_destinado_centavos = te.get(
                "valor_destinado_centavos"
            )

            if valor_destinado_centavos is not None:
                dados[
                    parlamentar
                ]["valor_destinado_centavos"] += (
                    valor_destinado_centavos
                )

            valor_transferido_centavos = te.get(
                "valor_transferido_centavos"
            )

            if valor_transferido_centavos is not None:
                dados[
                    parlamentar
                ]["valor_transferido_centavos"] += (
                    valor_transferido_centavos
                )

        resultado: list[dict[str, Any]] = []

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
                linha["valor_destinado_centavos"]
            ),
            reverse=True,
        )

    def resumo_planos_trabalho(
        self,
    ) -> dict[str, int]:
        """
        Resume indicadores não monetários dos Planos de Trabalho.

        Responde:
        - quantas TEs possuem PT aprovado;
        - quantas passaram por complementação;
        - quantas possuem relatório de gestão;
        - quantas ainda não possuem relatório de gestão;
        - quantas possuem múltiplos órgãos analisadores.
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

from __future__ import annotations

from copy import deepcopy
from typing import Any


class ConsolidacaoFinanceira:
    """
    Enriquece a f_transferencia com informações financeiras
    provenientes de fontes externas ao Transferegov.

    Granularidade:
        1 linha = 1 Plano de Ação / Transferência Especial.

    Fontes previstas:
        - Transferegov
        - Banco do Brasil
        - SIAFI/MG

    Regra fundamental:
        ausência de informação != zero.

    Portanto, valores ainda não obtidos permanecem como None.
    """

    def __init__(
        self,
        transferencias: list[dict[str, Any]],
        dados_bb: list[dict[str, Any]] | None = None,
        dados_siafi: list[dict[str, Any]] | None = None,
    ) -> None:
        self.transferencias = transferencias
        self.dados_bb = dados_bb or []
        self.dados_siafi = dados_siafi or []

    def consolidar(self) -> list[dict[str, Any]]:
        """
        Retorna uma nova lista, preservando a lista original.

        Nesta primeira versão, BB e SIAFI podem estar ausentes.
        """

        resultado = deepcopy(self.transferencias)

        indice_bb = self._criar_indice_bb()
        indice_siafi = self._criar_indice_siafi()

        for te in resultado:
            self._aplicar_bb(
                te=te,
                indice_bb=indice_bb,
            )

            self._aplicar_siafi(
                te=te,
                indice_siafi=indice_siafi,
            )

            self._calcular_indicadores_financeiros(te)

        return resultado

    # ==================================================
    # ÍNDICES
    # ==================================================

    def _criar_indice_bb(
        self,
    ) -> dict[str, dict[str, Any]]:
        """
        Indexa dados BB por agência/conta.

        Estrutura futura esperada:

        {
            "id_agencia_conta": "1615-27418",
            "saldo_investimento_bb": 12345.67,
            "valor_rendimentos": 456.78,
            "data_consulta_bb": "2026-08-27"
        }
        """

        indice: dict[str, dict[str, Any]] = {}

        for registro in self.dados_bb:
            chave = registro.get("id_agencia_conta")

            if chave:
                indice[str(chave)] = registro

        return indice

    def _criar_indice_siafi(
        self,
    ) -> dict[Any, dict[str, Any]]:
        """
        Indexa dados SIAFI pelo id_plano_acao.

        Esta chave poderá ser alterada futuramente caso
        a integração estadual utilize outra chave de ligação.
        """

        indice: dict[Any, dict[str, Any]] = {}

        for registro in self.dados_siafi:
            chave = registro.get("id_plano_acao")

            if chave is not None:
                indice[chave] = registro

        return indice

    # ==================================================
    # BANCO DO BRASIL
    # ==================================================

    @staticmethod
    def _aplicar_bb(
        te: dict[str, Any],
        indice_bb: dict[str, dict[str, Any]],
    ) -> None:
        chave = te.get("id_agencia_conta")

        # Campos explícitos para diferenciar:
        # "não consultado" de saldo zero.
        te["saldo_investimento_bb"] = None
        te["data_consulta_bb"] = None
        te["status_dados_bb"] = "NAO_DISPONIVEL"

        if not chave:
            te["status_dados_bb"] = "SEM_CONTA"
            return

        registro = indice_bb.get(str(chave))

        if registro is None:
            return

        te["saldo_investimento_bb"] = registro.get(
            "saldo_investimento_bb"
        )

        te["valor_rendimentos"] = registro.get(
            "valor_rendimentos"
        )

        te["data_consulta_bb"] = registro.get(
            "data_consulta_bb"
        )

        te["status_dados_bb"] = "DISPONIVEL"

    # ==================================================
    # SIAFI/MG
    # ==================================================

    @staticmethod
    def _aplicar_siafi(
        te: dict[str, Any],
        indice_siafi: dict[Any, dict[str, Any]],
    ) -> None:
        te["status_dados_siafi"] = "NAO_DISPONIVEL"

        id_plano_acao = te.get("id_plano_acao")

        registro = indice_siafi.get(id_plano_acao)

        if registro is None:
            return

        te["valor_empenhado"] = registro.get(
            "valor_empenhado"
        )

        te["valor_liquidado"] = registro.get(
            "valor_liquidado"
        )

        te["valor_pago"] = registro.get(
            "valor_pago"
        )

        te["status_dados_siafi"] = "DISPONIVEL"

    # ==================================================
    # INDICADORES FINANCEIROS
    # ==================================================

    @staticmethod
    def _calcular_indicadores_financeiros(
        te: dict[str, Any],
    ) -> None:
        valor_transferido = te.get(
            "valor_transferido"
        )

        valor_rendimentos = te.get(
            "valor_rendimentos"
        )

        valor_liquidado = te.get(
            "valor_liquidado"
        )

        # ----------------------------------------------
        # Recursos disponíveis
        # ----------------------------------------------
        #
        # Enquanto não conhecemos os rendimentos,
        # não afirmamos o total disponível.
        #
        if (
            valor_transferido is not None
            and valor_rendimentos is not None
        ):
            recursos_disponiveis = (
                float(valor_transferido)
                + float(valor_rendimentos)
            )
        else:
            recursos_disponiveis = None

        te["recursos_disponiveis"] = (
            recursos_disponiveis
        )

        # ----------------------------------------------
        # Valor executado
        # ----------------------------------------------
        #
        # Regra de negócio:
        # execução = liquidação.
        #
        if valor_liquidado is not None:
            valor_executado = float(
                valor_liquidado
            )
        else:
            valor_executado = None

        te["valor_executado"] = valor_executado

        # ----------------------------------------------
        # Valor a executar
        # ----------------------------------------------
        if (
            recursos_disponiveis is not None
            and valor_executado is not None
        ):
            te["valor_a_executar"] = (
                recursos_disponiveis
                - valor_executado
            )
        else:
            te["valor_a_executar"] = None

        # ----------------------------------------------
        # Percentual de execução
        # ----------------------------------------------
        if (
            recursos_disponiveis is not None
            and recursos_disponiveis != 0
            and valor_executado is not None
        ):
            te["percentual_execucao"] = (
                valor_executado
                / recursos_disponiveis
            )
        else:
            te["percentual_execucao"] = None
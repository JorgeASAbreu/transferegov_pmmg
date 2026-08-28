from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any

from transferegov.transformacao.moeda import para_centavos


class ConsolidacaoFinanceira:
    """
    Enriquece a f_transferencia com informações financeiras provenientes
    de fontes externas ao Transferegov.

    Granularidade:
        1 linha = 1 Plano de Ação / Transferência Especial.

    Fontes previstas:
        - Transferegov
        - Banco do Brasil
        - SIAFI/MG

    CONVENÇÃO MONETÁRIA OBRIGATÓRIA
    --------------------------------
    A camada analítica trabalha exclusivamente com valores monetários
    representados em CENTAVOS INTEIROS.

    Exemplos:
        1          = R$ 0,01
        100        = R$ 1,00
        123_456    = R$ 1.234,56
        52_735_000 = R$ 527.350,00

    Todo campo monetário analítico deve:
        - terminar com o sufixo "_centavos";
        - conter int ou None;
        - jamais conter float.

    REGRA FUNDAMENTAL
    -----------------
    ausência de informação != zero.

    Portanto:
        None significa "não conhecido / não disponível";
        0 significa um valor monetário conhecido igual a R$ 0,00.

    MANUTENÇÃO
    ----------
    - NÃO usar float em cálculos monetários.
    - NÃO usar int(valor * 100).
    - NÃO fazer multiplicações manuais por 100.
    - Valores externos em reais devem entrar por para_centavos(...).
    - Operações entre valores já convertidos são feitas diretamente
      com inteiros.
    - A conversão de centavos para reais pertence à apresentação.
    - Percentuais não são valores monetários e são calculados com
      Decimal para evitar propagação desnecessária de float.

    CONTRATO DAS FONTES EXTERNAS
    ----------------------------
    dados_bb e dados_siafi podem, nesta etapa da arquitetura, entregar
    valores em reais usando os nomes originais das fontes, por exemplo:

        valor_rendimentos
        saldo_investimento_bb
        valor_empenhado
        valor_liquidado
        valor_pago

    Esta classe é a fronteira responsável por converter esses valores
    para o padrão analítico em centavos.
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

        BB e SIAFI podem estar ausentes.

        A ausência dessas fontes não deve produzir zeros artificiais.
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
        Indexa dados do Banco do Brasil por agência/conta.

        Estrutura esperada nesta fronteira:

        {
            "id_agencia_conta": "1615-27418",
            "saldo_investimento_bb": 12345.67,
            "valor_rendimentos": 456.78,
            "data_consulta_bb": "2026-08-27"
        }

        Os valores monetários acima ainda estão expressos em reais.
        A conversão para centavos ocorre em _aplicar_bb().
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
        Indexa dados SIAFI/MG pelo id_plano_acao.

        Estrutura monetária esperada nesta fronteira:

        {
            "id_plano_acao": 92176,
            "valor_empenhado": 400000.00,
            "valor_liquidado": 250000.00,
            "valor_pago": 200000.00
        }

        Esses valores são convertidos para centavos em _aplicar_siafi().

        A chave poderá ser alterada futuramente caso a integração
        estadual utilize outra chave de ligação.
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
        """
        Incorpora dados bancários à transferência.

        Todos os valores monetários são convertidos para centavos
        antes de entrarem no modelo analítico.
        """
        chave = te.get("id_agencia_conta")

        # Inicialização explícita.
        #
        # None significa "informação não disponível".
        # Nunca substituir None por zero apenas para facilitar cálculo.
        te["saldo_investimento_bb_centavos"] = None
        te["valor_rendimentos_centavos"] = None
        te["data_consulta_bb"] = None
        te["status_dados_bb"] = "NAO_DISPONIVEL"

        if not chave:
            te["status_dados_bb"] = "SEM_CONTA"
            return

        registro = indice_bb.get(str(chave))

        if registro is None:
            return

        te["saldo_investimento_bb_centavos"] = para_centavos(
            registro.get("saldo_investimento_bb")
        )

        te["valor_rendimentos_centavos"] = para_centavos(
            registro.get("valor_rendimentos")
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
        """
        Incorpora execução orçamentária/financeira estadual.

        Regra de negócio do projeto:
            valor executado = valor liquidado.

        Todos os valores monetários entram na camada analítica em
        centavos inteiros.
        """
        te["valor_empenhado_centavos"] = None
        te["valor_liquidado_centavos"] = None
        te["valor_pago_centavos"] = None
        te["status_dados_siafi"] = "NAO_DISPONIVEL"

        id_plano_acao = te.get("id_plano_acao")

        registro = indice_siafi.get(id_plano_acao)

        if registro is None:
            return

        te["valor_empenhado_centavos"] = para_centavos(
            registro.get("valor_empenhado")
        )

        te["valor_liquidado_centavos"] = para_centavos(
            registro.get("valor_liquidado")
        )

        te["valor_pago_centavos"] = para_centavos(
            registro.get("valor_pago")
        )

        te["status_dados_siafi"] = "DISPONIVEL"

    # ==================================================
    # INDICADORES FINANCEIROS
    # ==================================================

    @staticmethod
    def _calcular_indicadores_financeiros(
        te: dict[str, Any],
    ) -> None:
        """
        Calcula os indicadores financeiros derivados.

        Todas as operações monetárias abaixo usam apenas int.

        Fórmulas:
            recursos_disponiveis
                = valor_transferido + valor_rendimentos

            valor_executado
                = valor_liquidado

            liquidado_a_pagar
                = valor_liquidado - valor_pago

            saldo_financeiro_teorico
                = recursos_disponiveis - valor_pago

            valor_a_executar
                = recursos_disponiveis - valor_liquidado

            percentual_execucao
                = valor_liquidado / recursos_disponiveis

        Identidade de consistência:
            saldo_financeiro_teorico - valor_a_executar
                = liquidado_a_pagar

        A identidade somente pode ser verificada quando todos os
        componentes necessários estão disponíveis.
        """
        valor_transferido_centavos = te.get(
            "valor_transferido_centavos"
        )

        valor_rendimentos_centavos = te.get(
            "valor_rendimentos_centavos"
        )

        valor_liquidado_centavos = te.get(
            "valor_liquidado_centavos"
        )

        valor_pago_centavos = te.get(
            "valor_pago_centavos"
        )

        # ----------------------------------------------
        # Recursos disponíveis
        # ----------------------------------------------
        #
        # Enquanto os rendimentos forem desconhecidos,
        # não afirmamos o total disponível.
        #
        if (
            valor_transferido_centavos is not None
            and valor_rendimentos_centavos is not None
        ):
            recursos_disponiveis_centavos = (
                valor_transferido_centavos
                + valor_rendimentos_centavos
            )
        else:
            recursos_disponiveis_centavos = None

        te["recursos_disponiveis_centavos"] = (
            recursos_disponiveis_centavos
        )

        # ----------------------------------------------
        # Valor executado
        # ----------------------------------------------
        #
        # Regra de negócio:
        # execução = liquidação.
        #
        valor_executado_centavos = (
            valor_liquidado_centavos
            if valor_liquidado_centavos is not None
            else None
        )

        te["valor_executado_centavos"] = (
            valor_executado_centavos
        )

        # ----------------------------------------------
        # Liquidado a pagar
        # ----------------------------------------------
        if (
            valor_liquidado_centavos is not None
            and valor_pago_centavos is not None
        ):
            liquidado_a_pagar_centavos = (
                valor_liquidado_centavos
                - valor_pago_centavos
            )
        else:
            liquidado_a_pagar_centavos = None

        te["liquidado_a_pagar_centavos"] = (
            liquidado_a_pagar_centavos
        )

        # ----------------------------------------------
        # Saldo financeiro teórico
        # ----------------------------------------------
        #
        # Este campo representa uma inferência contábil/financeira:
        #
        # recursos disponíveis - pagamentos estaduais.
        #
        # Ele NÃO deve ser confundido com saldo bancário observado.
        #
        if (
            recursos_disponiveis_centavos is not None
            and valor_pago_centavos is not None
        ):
            saldo_financeiro_teorico_centavos = (
                recursos_disponiveis_centavos
                - valor_pago_centavos
            )
        else:
            saldo_financeiro_teorico_centavos = None

        te["saldo_financeiro_teorico_centavos"] = (
            saldo_financeiro_teorico_centavos
        )

        # ----------------------------------------------
        # Valor a executar
        # ----------------------------------------------
        #
        # Perspectiva da execução:
        # recursos disponíveis que ainda não foram liquidados.
        #
        if (
            recursos_disponiveis_centavos is not None
            and valor_executado_centavos is not None
        ):
            valor_a_executar_centavos = (
                recursos_disponiveis_centavos
                - valor_executado_centavos
            )
        else:
            valor_a_executar_centavos = None

        te["valor_a_executar_centavos"] = (
            valor_a_executar_centavos
        )

        # ----------------------------------------------
        # Percentual de execução
        # ----------------------------------------------
        #
        # Percentual não é dinheiro.
        #
        # Usamos Decimal para evitar o retorno automático a float.
        # O valor permanece como razão:
        #
        #     0.50 = 50%
        #
        # A formatação percentual pertence à apresentação.
        #
        if (
            recursos_disponiveis_centavos is not None
            and recursos_disponiveis_centavos != 0
            and valor_executado_centavos is not None
        ):
            te["percentual_execucao"] = (
                Decimal(valor_executado_centavos)
                / Decimal(recursos_disponiveis_centavos)
            )
        else:
            te["percentual_execucao"] = None

        # ----------------------------------------------
        # Verificação interna de consistência
        # ----------------------------------------------
        #
        # Não classifica irregularidade.
        # Apenas verifica uma identidade matemática entre os
        # indicadores calculados por esta própria classe.
        #
        if (
            saldo_financeiro_teorico_centavos is not None
            and valor_a_executar_centavos is not None
            and liquidado_a_pagar_centavos is not None
        ):
            te["consistencia_financeira_interna"] = (
                (
                    saldo_financeiro_teorico_centavos
                    - valor_a_executar_centavos
                )
                == liquidado_a_pagar_centavos
            )
        else:
            te["consistencia_financeira_interna"] = None

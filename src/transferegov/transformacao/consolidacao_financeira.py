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
    ) -> dict[str, dict[Any, dict[str, Any]]]:
        """
        Cria dois índices para compatibilidade e rastreabilidade:

        por_plano:
            id_plano_acao -> resultado da conta EXECUTOR no BB.

        legado_por_conta:
            id_agencia_conta -> formato antigo de mocks/testes.

        O vínculo de produção é por id_plano_acao, obtido da lista
        "planos_acao" gravada em cada resultado da conta executor.

        Isso é importante porque a conta operacional consultada no BB
        é a conta do executor, e não a conta bancária do Plano de Ação.
        """
        por_plano: dict[Any, dict[str, Any]] = {}
        legado_por_conta: dict[str, dict[str, Any]] = {}

        for registro in self.dados_bb:
            planos = registro.get("planos_acao")

            if isinstance(planos, list):
                for plano in planos:
                    if not isinstance(plano, dict):
                        continue

                    id_plano_acao = plano.get("id_plano_acao")

                    if id_plano_acao is not None:
                        por_plano[id_plano_acao] = registro

            # Compatibilidade temporária com testes/mocks V5
            # anteriores ao uso da conta executor.
            chave_legada = registro.get("id_agencia_conta")

            if chave_legada:
                legado_por_conta[str(chave_legada)] = registro

        return {
            "por_plano": por_plano,
            "legado_por_conta": legado_por_conta,
        }

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
        indice_bb: dict[str, dict[Any, dict[str, Any]]],
    ) -> None:
        """
        Incorpora os dados do Banco do Brasil à Transferência Especial.

        REGRA DE VÍNCULO
        ----------------
        Produção:
            id_plano_acao
                -> conta executor
                -> resultado da API BB

        A conta do Plano de Ação não é usada como conta operacional
        para consulta bancária.

        REGRA DE QUALIDADE
        ------------------
        OK e SEM_FUNDOS:
            verificacao_manual_bb = False

        Qualquer outro status:
            verificacao_manual_bb = True
            valores bancários permanecem None
            código/mensagem da API são preservados.

        REGRA DE CONTA COMPARTILHADA
        ----------------------------
        Uma conta executor pode estar vinculada a mais de uma TE.

        Quando isso ocorrer:
        - o saldo observado no BB continua pertencendo à CONTA;
        - o saldo total da conta NÃO é atribuído individualmente
          a nenhuma TE;
        - saldo_investimento_bb_conta_centavos preserva o valor
          observado no nível bancário;
        - saldo_investimento_bb_centavos fica None no nível da TE;
        - saldo_bb_atribuivel_te = False;
        - verificacao_manual_bb continua False se a API respondeu OK,
          pois compartilhamento não é erro da API.

        Isso impede dupla ou múltipla contagem do mesmo dinheiro em
        agregações por Transferência Especial.

        Ausência de informação nunca é convertida em zero.
        """
        te["id_agencia_conta_executor"] = None
        te["agencia_executor_bb"] = None
        te["conta_executor_bb"] = None

        # Saldo observado na conta bancária, independentemente de ser
        # atribuível a uma TE específica.
        te["saldo_investimento_bb_conta_centavos"] = None

        # Saldo que pode ser atribuído com segurança à TE.
        te["saldo_investimento_bb_centavos"] = None

        te["valor_rendimentos_centavos"] = None
        te["data_consulta_bb"] = None

        te["status_dados_bb"] = "NAO_DISPONIVEL"
        te["verificacao_manual_bb"] = True
        te["codigo_erro_api_bb"] = None
        te["mensagem_erro_api_bb"] = None
        te["status_http_bb"] = None

        te["quantidade_tes_conta_executor"] = None
        te["conta_executor_compartilhada"] = None
        te["saldo_bb_atribuivel_te"] = False
        te["motivo_saldo_nao_atribuido"] = (
            "DADOS_BB_NAO_DISPONIVEIS"
        )

        id_plano_acao = te.get("id_plano_acao")

        registro = indice_bb["por_plano"].get(id_plano_acao)

        # Compatibilidade com mocks antigos do projeto.
        if registro is None:
            chave_legada = te.get("id_agencia_conta")

            if chave_legada:
                registro = indice_bb[
                    "legado_por_conta"
                ].get(str(chave_legada))

        if registro is None:
            te["status_dados_bb"] = "SEM_RESULTADO_BB"
            te["motivo_saldo_nao_atribuido"] = (
                "SEM_RESULTADO_BB"
            )
            return

        te["id_agencia_conta_executor"] = registro.get(
            "id_agencia_conta_executor"
        )
        te["agencia_executor_bb"] = registro.get("agencia")
        te["conta_executor_bb"] = registro.get("conta")

        consultado_em = registro.get("consultado_em")
        te["data_consulta_bb"] = (
            consultado_em
            or registro.get("data_consulta_bb")
        )

        quantidade_planos = registro.get(
            "quantidade_planos_acao"
        )

        if quantidade_planos is None:
            planos = registro.get("planos_acao")

            if isinstance(planos, list):
                quantidade_planos = len(planos)

        if quantidade_planos is not None:
            try:
                quantidade_planos = int(quantidade_planos)
            except (TypeError, ValueError):
                quantidade_planos = None

        te["quantidade_tes_conta_executor"] = (
            quantidade_planos
        )

        compartilhada = bool(
            quantidade_planos is not None
            and quantidade_planos > 1
        )

        te["conta_executor_compartilhada"] = (
            compartilhada
        )

        status = registro.get("status_consulta")

        # Compatibilidade com mocks antigos sem status.
        if status is None and (
            "saldo_investimento_bb" in registro
            or "valor_rendimentos" in registro
        ):
            status = "OK"

        te["status_dados_bb"] = (
            status
            if status is not None
            else "NAO_DISPONIVEL"
        )

        te["status_http_bb"] = registro.get(
            "status_http_bb"
        )
        te["codigo_erro_api_bb"] = registro.get(
            "codigo_erro_api_bb"
        )
        te["mensagem_erro_api_bb"] = registro.get(
            "mensagem_erro_api_bb"
        )

        status_valido = status in {
            "OK",
            "SEM_FUNDOS",
        }

        te["verificacao_manual_bb"] = not status_valido

        # Se o lote já informou explicitamente verificação manual,
        # preservamos True em caso de divergência.
        if registro.get("verificacao_manual_bb") is True:
            te["verificacao_manual_bb"] = True

        if not status_valido:
            te["motivo_saldo_nao_atribuido"] = (
                "DADOS_BB_INDISPONIVEIS"
            )
            return

        if status == "SEM_FUNDOS":
            # Consulta válida, porém nenhum fundo foi retornado.
            # Não inferimos saldo zero.
            te["motivo_saldo_nao_atribuido"] = (
                "SEM_FUNDOS"
            )
            return

        # ----------------------------------------------------------
        # SALDO BANCÁRIO OBSERVADO
        # ----------------------------------------------------------
        saldo_conta_centavos = registro.get(
            "saldo_investimento_bb_centavos"
        )

        if saldo_conta_centavos is not None:
            if (
                isinstance(saldo_conta_centavos, bool)
                or not isinstance(saldo_conta_centavos, int)
            ):
                raise TypeError(
                    "saldo_investimento_bb_centavos deve ser "
                    "int ou None."
                )

            te["saldo_investimento_bb_conta_centavos"] = (
                saldo_conta_centavos
            )

        # Compatibilidade com formato antigo em reais.
        if (
            te["saldo_investimento_bb_conta_centavos"] is None
            and registro.get("saldo_investimento_bb") is not None
        ):
            te["saldo_investimento_bb_conta_centavos"] = (
                para_centavos(
                    registro.get("saldo_investimento_bb")
                )
            )

        # ----------------------------------------------------------
        # BLINDAGEM CONTRA DUPLA CONTAGEM
        # ----------------------------------------------------------
        if compartilhada:
            te["saldo_bb_atribuivel_te"] = False
            te["saldo_investimento_bb_centavos"] = None
            te["motivo_saldo_nao_atribuido"] = (
                "CONTA_EXECUTOR_COMPARTILHADA"
            )
        else:
            te["saldo_bb_atribuivel_te"] = True
            te["saldo_investimento_bb_centavos"] = (
                te["saldo_investimento_bb_conta_centavos"]
            )
            te["motivo_saldo_nao_atribuido"] = None

        # Rendimentos ainda não são calculados pelo endpoint de saldo.
        # Caso uma fonte específica os forneça, a mesma regra de
        # atribuição deverá ser aplicada antes de colocá-los no nível TE.
        rendimentos_centavos = registro.get(
            "valor_rendimentos_centavos"
        )

        if rendimentos_centavos is not None:
            if (
                isinstance(rendimentos_centavos, bool)
                or not isinstance(rendimentos_centavos, int)
            ):
                raise TypeError(
                    "valor_rendimentos_centavos deve ser "
                    "int ou None."
                )

            if not compartilhada:
                te["valor_rendimentos_centavos"] = (
                    rendimentos_centavos
                )

        if (
            te["valor_rendimentos_centavos"] is None
            and not compartilhada
            and registro.get("valor_rendimentos") is not None
        ):
            te["valor_rendimentos_centavos"] = (
                para_centavos(
                    registro.get("valor_rendimentos")
                )
            )

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

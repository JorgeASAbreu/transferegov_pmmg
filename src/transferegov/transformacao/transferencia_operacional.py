from __future__ import annotations

import unicodedata
from collections import defaultdict
from typing import Any

from transferegov.transformacao.moeda import para_centavos


class TransferenciaOperacionalExecutor:
    """
    Identifica, com evidência auditável, o valor efetivamente
    transferido para a conta operacional do executor.

    OBJETIVO
    --------
    Esta camada NÃO substitui ainda o cálculo consolidado da
    f_transferencia. Ela existe para validar a nova regra de negócio
    antes de alterar o valor_transferido_centavos oficial.

    REGRA DE NEGÓCIO
    ----------------
    Para a PMMG, o valor operacional relevante é o recurso que chega
    à conta do EXECUTOR, e não simplesmente o total da cadeia federal
    Plano de Ação -> Empenho -> Documento Hábil -> OP/OB.

    Uma transferência interna é candidata somente quando TODAS as
    condições abaixo são atendidas:

    1. descricao_gestao_financeira == "Transferência enviada";
    2. tipo_operacao_gestao_financeira == "D";
    3. CNPJ favorecido == CNPJ do executor;
    4. numero_referencia_unica_gestao_financeira identifica
       exatamente a agência/conta do executor.

    REFERÊNCIA BB
    -------------
    O padrão observado na base é:

        55 + agência(4 posições) + conta(9 posições, zero à esquerda)

    Exemplo:
        agência 1615
        conta   26885

        referência esperada:
        551615000026885

    CLASSIFICAÇÃO DO PRINCIPAL
    --------------------------
    O valor previsto do executor é:

        vl_custeio_executor + vl_investimento_executor

    Entre as transferências candidatas, o PRINCIPAL somente é
    confirmado quando existe EXATAMENTE UMA movimentação cujo valor
    seja idêntico ao valor previsto do executor.

    Qualquer movimentação candidata excedente NÃO é automaticamente
    classificada como rendimento. Ela permanece separada como
    "movimentação adicional não classificada" até que outra fonte
    forneça evidência suficiente.

    CONVENÇÃO MONETÁRIA
    -------------------
    Todo valor analítico retornado por esta classe está em CENTAVOS
    INTEIROS. Nunca é utilizado float em cálculos monetários.

    STATUS
    ------
    CONFIRMADA
        Uma única transferência candidata coincide exatamente com o
        valor previsto do executor.

    SEM_EVIDENCIA_TRANSFERENCIA
        Não foi encontrada movimentação que satisfaça os critérios
        documentais da transferência para a conta executor.

    DIVERGENTE_VALOR_EXECUTOR
        Há movimentações candidatas, mas nenhuma coincide com o valor
        previsto do executor.

    AMBIGUA_MULTIPLAS_PRINCIPAIS
        Mais de uma movimentação candidata coincide com o valor
        previsto. O sistema não escolhe arbitrariamente.

    SEM_VALOR_PREVISTO_EXECUTOR
        Não há valor de custeio/investimento suficiente para construir
        o valor previsto do executor.

    IMPORTANTE
    ----------
    None significa ausência de informação ou impossibilidade de
    atribuição segura. Nunca significa R$ 0,00.
    """

    STATUS_CONFIRMADA = "CONFIRMADA"
    STATUS_SEM_EVIDENCIA = "SEM_EVIDENCIA_TRANSFERENCIA"
    STATUS_DIVERGENTE = "DIVERGENTE_VALOR_EXECUTOR"
    STATUS_AMBIGUA = "AMBIGUA_MULTIPLAS_PRINCIPAIS"
    STATUS_SEM_VALOR_PREVISTO = "SEM_VALOR_PREVISTO_EXECUTOR"

    def __init__(
        self,
        tabelas: dict[str, list[dict[str, Any]]],
    ) -> None:
        self.executores = tabelas.get("executores", [])
        self.lancamentos = tabelas.get(
            "lancamentos_financeiros",
            [],
        )

    def analisar(self) -> list[dict[str, Any]]:
        """
        Retorna uma linha analítica por executor/plano de ação.
        """
        lancamentos_por_plano: dict[Any, list[dict[str, Any]]] = (
            defaultdict(list)
        )

        for lancamento in self.lancamentos:
            lancamentos_por_plano[
                lancamento.get("id_plano_acao")
            ].append(lancamento)

        resultado: list[dict[str, Any]] = []

        for executor in self.executores:
            id_plano_acao = executor.get("id_plano_acao")

            resultado.append(
                self._analisar_executor(
                    executor=executor,
                    lancamentos=lancamentos_por_plano.get(
                        id_plano_acao,
                        [],
                    ),
                )
            )

        return resultado

    def _analisar_executor(
        self,
        executor: dict[str, Any],
        lancamentos: list[dict[str, Any]],
    ) -> dict[str, Any]:
        id_plano_acao = executor.get("id_plano_acao")
        id_executor = executor.get("id_executor")

        agencia = self._somente_digitos(
            executor.get("numero_agencia_executor")
        )
        conta = self._somente_digitos(
            executor.get("numero_conta_executor")
        )
        cnpj_executor = self._normalizar_documento(
            executor.get("cnpj_executor")
        )

        valor_previsto = self._valor_previsto_executor(
            executor
        )

        referencia_esperada = self._referencia_bb_esperada(
            agencia=agencia,
            conta=conta,
        )

        candidatos = [
            lancamento
            for lancamento in lancamentos
            if self._eh_transferencia_para_executor(
                lancamento=lancamento,
                cnpj_executor=cnpj_executor,
                referencia_esperada=referencia_esperada,
            )
        ]

        base = {
            "id_plano_acao": id_plano_acao,
            "id_executor": id_executor,
            "cnpj_executor": cnpj_executor,
            "agencia_executor": agencia or None,
            "conta_executor": conta or None,
            "id_agencia_conta_executor": (
                f"{agencia}-{conta}"
                if agencia and conta
                else None
            ),
            "referencia_bb_esperada": (
                referencia_esperada or None
            ),
            "valor_previsto_executor_centavos": (
                valor_previsto
            ),
            "quantidade_transferencias_candidatas": len(
                candidatos
            ),
            "valor_transferido_operacional_centavos": None,
            "origem_valor_transferido_operacional": None,
            "status_transferencia_operacional": None,
            "verificacao_manual_transferencia_operacional": True,
            "ids_lancamentos_principal": [],
            "ids_lancamentos_adicionais": [],
            "quantidade_movimentacoes_adicionais": None,
            "valor_movimentacoes_adicionais_executor_centavos": None,
            "tem_movimentacao_adicional_executor": None,
            "verificacao_manual_movimentacao_adicional": False,
        }

        if valor_previsto is None:
            base["status_transferencia_operacional"] = (
                self.STATUS_SEM_VALOR_PREVISTO
            )
            return base

        if not candidatos:
            base["status_transferencia_operacional"] = (
                self.STATUS_SEM_EVIDENCIA
            )
            return base

        candidatos_com_valor: list[
            tuple[dict[str, Any], int]
        ] = []

        for lancamento in candidatos:
            valor_centavos = para_centavos(
                lancamento.get(
                    "valor_gestao_financeira"
                )
            )

            if valor_centavos is None:
                continue

            candidatos_com_valor.append(
                (lancamento, valor_centavos)
            )

        principais = [
            (lancamento, valor_centavos)
            for lancamento, valor_centavos
            in candidatos_com_valor
            if valor_centavos == valor_previsto
        ]

        if len(principais) == 0:
            base["status_transferencia_operacional"] = (
                self.STATUS_DIVERGENTE
            )
            return base

        if len(principais) > 1:
            base["status_transferencia_operacional"] = (
                self.STATUS_AMBIGUA
            )
            base["ids_lancamentos_principal"] = [
                item[0].get(
                    "id_lancamento_gestao_financeira"
                )
                for item in principais
            ]
            return base

        principal, valor_principal = principais[0]

        adicionais = [
            (lancamento, valor_centavos)
            for lancamento, valor_centavos
            in candidatos_com_valor
            if lancamento is not principal
        ]

        valor_adicional = sum(
            valor_centavos
            for _, valor_centavos in adicionais
        )

        base.update(
            {
                "valor_transferido_operacional_centavos": (
                    valor_principal
                ),
                "origem_valor_transferido_operacional": (
                    "GESTAO_FINANCEIRA_TRANSFERENCIA_EXECUTOR"
                ),
                "status_transferencia_operacional": (
                    self.STATUS_CONFIRMADA
                ),
                "verificacao_manual_transferencia_operacional": False,
                "ids_lancamentos_principal": [
                    principal.get(
                        "id_lancamento_gestao_financeira"
                    )
                ],
                "ids_lancamentos_adicionais": [
                    item[0].get(
                        "id_lancamento_gestao_financeira"
                    )
                    for item in adicionais
                ],
                "quantidade_movimentacoes_adicionais": len(
                    adicionais
                ),
                "valor_movimentacoes_adicionais_executor_centavos": (
                    valor_adicional
                ),
                "tem_movimentacao_adicional_executor": bool(
                    adicionais
                ),
                "verificacao_manual_movimentacao_adicional": bool(
                    adicionais
                ),
            }
        )

        return base

    @staticmethod
    def _valor_previsto_executor(
        executor: dict[str, Any],
    ) -> int | None:
        """
        Soma custeio + investimento do executor em centavos.

        Se ambos estiverem ausentes, o resultado é None.
        Se apenas um estiver presente, o componente ausente equivale
        a zero somente dentro desta composição.
        """
        custeio_bruto = executor.get("vl_custeio_executor")
        investimento_bruto = executor.get(
            "vl_investimento_executor"
        )

        if (
            custeio_bruto is None
            and investimento_bruto is None
        ):
            return None

        custeio = (
            para_centavos(custeio_bruto)
            if custeio_bruto is not None
            else 0
        )
        investimento = (
            para_centavos(investimento_bruto)
            if investimento_bruto is not None
            else 0
        )

        return (custeio or 0) + (investimento or 0)

    @classmethod
    def _eh_transferencia_para_executor(
        cls,
        lancamento: dict[str, Any],
        cnpj_executor: str,
        referencia_esperada: str,
    ) -> bool:
        if not cnpj_executor or not referencia_esperada:
            return False

        descricao = cls._normalizar_texto(
            lancamento.get(
                "descricao_gestao_financeira"
            )
        )

        tipo = str(
            lancamento.get(
                "tipo_operacao_gestao_financeira"
            )
            or ""
        ).strip().upper()

        cnpj_favorecido = cls._normalizar_documento(
            lancamento.get(
                "doc_favorecido_gestao_financeira"
            )
        )

        referencia = cls._somente_digitos(
            lancamento.get(
                "numero_referencia_unica_gestao_financeira"
            )
        )

        return (
            descricao == "transferencia enviada"
            and tipo == "D"
            and cnpj_favorecido == cnpj_executor
            and referencia == referencia_esperada
        )

    @staticmethod
    def _referencia_bb_esperada(
        agencia: str,
        conta: str,
    ) -> str:
        if not agencia or not conta:
            return ""

        return (
            "55"
            + agencia.zfill(4)
            + conta.zfill(9)
        )

    @staticmethod
    def _normalizar_documento(valor: Any) -> str:
        """
        Normaliza CNPJ inclusive quando a origem o serializa como
        string decimal, por exemplo: "16695025000197.0".
        """
        if valor is None:
            return ""

        texto = str(valor).strip()

        if texto.endswith(".0"):
            texto = texto[:-2]

        return "".join(
            caractere
            for caractere in texto
            if caractere.isdigit()
        )

    @staticmethod
    def _somente_digitos(valor: Any) -> str:
        if valor is None:
            return ""

        return "".join(
            caractere
            for caractere in str(valor).strip()
            if caractere.isdigit()
        )

    @staticmethod
    def _normalizar_texto(valor: Any) -> str:
        texto = str(valor or "").strip().lower()

        texto = unicodedata.normalize(
            "NFKD",
            texto,
        )

        return "".join(
            caractere
            for caractere in texto
            if not unicodedata.combining(caractere)
        )

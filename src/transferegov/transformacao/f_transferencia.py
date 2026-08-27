from __future__ import annotations

from collections import defaultdict
from typing import Any


class FTransferencia:
    """
    Constrói a tabela analítica f_transferencia.

    Granularidade:
        1 linha = 1 Plano de Ação / Transferência Especial.

    Regras importantes:

    1. valor_transferido:
       obtido pela cadeia federal:
       Plano de Ação -> Empenho -> Documento Hábil -> OP/OB.

    2. Gestão Financeira:
       - até 2024, uma conta pode estar vinculada a várias TEs;
       - a partir de 2025, considera-se 1 TE = 1 conta.

    Portanto, saldo e movimentação bancária anterior a 2025
    não devem ser interpretados automaticamente como exclusivos
    de uma única TE.
    """

    ANO_INICIO_CONTA_EXCLUSIVA = 2025

    def __init__(
        self,
        tabelas: dict[str, list[dict[str, Any]]],
    ) -> None:
        self.tabelas = tabelas

        self.planos_acao = tabelas.get(
            "planos_acao",
            [],
        )

        self.planos_trabalho = tabelas.get(
            "planos_trabalho",
            [],
        )

        self.historico_planos_trabalho = tabelas.get(
            "historico_planos_trabalho",
            [],
        )

        self.metas = tabelas.get(
            "metas",
            [],
        )

        self.analises = tabelas.get(
            "analises",
            [],
        )

        self.relatorios = tabelas.get(
            "relatorios_gestao",
            [],
        )

        self.empenhos = tabelas.get(
            "empenhos",
            [],
        )

        self.documentos_habeis = tabelas.get(
            "documentos_habeis",
            [],
        )

        self.op_ob = tabelas.get(
            "op_ob",
            [],
        )

        self.lancamentos = tabelas.get(
            "lancamentos_financeiros",
            [],
        )

        self.saldos = tabelas.get(
            "saldos_conta",
            [],
        )

        self.programas = tabelas.get(
            "programas",
            [],
        )

        self.beneficiarios = tabelas.get(
            "beneficiarios",
            [],
        )

    # ==================================================
    # CONSTRUÇÃO
    # ==================================================

    def construir(
        self,
    ) -> list[dict[str, Any]]:
        resultado: list[dict[str, Any]] = []

        indices = self._criar_indices()

        for plano in self.planos_acao:
            id_plano_acao = plano.get(
                "id_plano_acao"
            )

            if id_plano_acao is None:
                continue

            resultado.append(
                self._construir_linha(
                    plano=plano,
                    indices=indices,
                )
            )

        return resultado

    # ==================================================
    # ÍNDICES
    # ==================================================

    def _criar_indices(
        self,
    ) -> dict[str, Any]:
        planos_trabalho_por_plano = defaultdict(list)
        historico_pt_por_pt = defaultdict(list)
        metas_por_plano = defaultdict(list)
        analises_por_plano = defaultdict(list)
        relatorios_por_plano = defaultdict(list)

        empenhos_por_plano = defaultdict(list)
        dh_por_empenho = defaultdict(list)
        op_ob_por_dh = defaultdict(list)

        lancamentos_por_plano = defaultdict(list)
        saldos_por_plano = defaultdict(list)

        planos_por_conta = defaultdict(list)

        for registro in self.planos_trabalho:
            planos_trabalho_por_plano[
                registro.get("id_plano_acao")
            ].append(registro)

        for registro in self.historico_planos_trabalho:
            historico_pt_por_pt[
                registro.get("id_plano_trabalho")
            ].append(registro)

        for registro in self.metas:
            metas_por_plano[
                registro.get("id_plano_acao")
            ].append(registro)

        for registro in self.analises:
            analises_por_plano[
                registro.get("id_plano_acao")
            ].append(registro)

        for registro in self.relatorios:
            relatorios_por_plano[
                registro.get("id_plano_acao")
            ].append(registro)

        for registro in self.empenhos:
            empenhos_por_plano[
                registro.get("id_plano_acao")
            ].append(registro)

        for registro in self.documentos_habeis:
            dh_por_empenho[
                registro.get("id_empenho")
            ].append(registro)

        for registro in self.op_ob:
            op_ob_por_dh[
                registro.get("id_dh")
            ].append(registro)

        for registro in self.lancamentos:
            lancamentos_por_plano[
                registro.get("id_plano_acao")
            ].append(registro)

        for registro in self.saldos:
            saldos_por_plano[
                registro.get("id_plano_acao")
            ].append(registro)

        for plano in self.planos_acao:
            id_agencia_conta = plano.get(
                "id_agencia_conta"
            )

            if id_agencia_conta:
                planos_por_conta[
                    id_agencia_conta
                ].append(
                    plano.get(
                        "id_plano_acao"
                    )
                )

        programas_por_id = {
            registro.get("id_programa"): registro
            for registro in self.programas
            if registro.get("id_programa") is not None
        }

        beneficiarios_por_id = {
            registro.get("id_beneficiario"): registro
            for registro in self.beneficiarios
            if registro.get("id_beneficiario") is not None
        }

        return {
            "planos_trabalho_por_plano": (
                planos_trabalho_por_plano
            ),
            "historico_pt_por_pt": (
                historico_pt_por_pt
            ),
            "metas_por_plano": metas_por_plano,
            "analises_por_plano": analises_por_plano,
            "relatorios_por_plano": relatorios_por_plano,
            "empenhos_por_plano": empenhos_por_plano,
            "dh_por_empenho": dh_por_empenho,
            "op_ob_por_dh": op_ob_por_dh,
            "lancamentos_por_plano": lancamentos_por_plano,
            "saldos_por_plano": saldos_por_plano,
            "planos_por_conta": planos_por_conta,
            "programas_por_id": programas_por_id,
            "beneficiarios_por_id": beneficiarios_por_id,
        }

    # ==================================================
    # LINHA DA TRANSFERÊNCIA
    # ==================================================

    def _construir_linha(
        self,
        plano: dict[str, Any],
        indices: dict[str, Any],
    ) -> dict[str, Any]:
        id_plano_acao = plano[
            "id_plano_acao"
        ]

        ano_plano_acao = plano.get(
            "ano_plano_acao"
        )

        id_agencia_conta = plano.get(
            "id_agencia_conta"
        )

        planos_trabalho = (
            indices[
                "planos_trabalho_por_plano"
            ].get(
                id_plano_acao,
                [],
            )
        )

        metas = (
            indices[
                "metas_por_plano"
            ].get(
                id_plano_acao,
                [],
            )
        )

        analises = (
            indices[
                "analises_por_plano"
            ].get(
                id_plano_acao,
                [],
            )
        )

        relatorios = (
            indices[
                "relatorios_por_plano"
            ].get(
                id_plano_acao,
                [],
            )
        )

        empenhos = (
            indices[
                "empenhos_por_plano"
            ].get(
                id_plano_acao,
                [],
            )
        )

        lancamentos = (
            indices[
                "lancamentos_por_plano"
            ].get(
                id_plano_acao,
                [],
            )
        )

        saldos = (
            indices[
                "saldos_por_plano"
            ].get(
                id_plano_acao,
                [],
            )
        )

        programa = (
            indices[
                "programas_por_id"
            ].get(
                plano.get("id_programa")
            )
        )

        beneficiario = (
            indices[
                "beneficiarios_por_id"
            ].get(
                plano.get("id_beneficiario")
            )
        )

        conta_compartilhada = (
            self._conta_compartilhada(
                id_agencia_conta=id_agencia_conta,
                ano_plano_acao=ano_plano_acao,
                planos_por_conta=indices[
                    "planos_por_conta"
                ],
            )
        )

        saldo_confiavel_te = (
            not conta_compartilhada
        )

        valor_destinado = (
            self._calcular_valor_destinado(
                plano
            )
        )

        valor_transferido = (
            self._calcular_valor_transferido_federal(
                empenhos=empenhos,
                dh_por_empenho=indices[
                    "dh_por_empenho"
                ],
                op_ob_por_dh=indices[
                    "op_ob_por_dh"
                ],
            )
        )

        saldo_conta = (
            self._obter_saldo_mais_recente(
                saldos
            )
        )

        data_saldo = (
            self._obter_data_saldo_mais_recente(
                saldos
            )
        )

        data_deposito = (
            self._obter_data_primeiro_deposito(
                lancamentos
            )
        )

        quantidade_orgaos = (
            self._quantidade_orgaos_analisadores(
                analises
            )
        )

        teve_complementacao = (
            self._teve_complementacao(
                planos_trabalho,
                analises,
                indices[
                    "historico_pt_por_pt"
                ],
            )
        )

        return {
            # ==========================================
            # IDENTIFICAÇÃO
            # ==========================================
            "id_plano_acao": id_plano_acao,

            "codigo_plano_acao": plano.get(
                "codigo_plano_acao"
            ),

            "ano_plano_acao": ano_plano_acao,

            "situacao_plano_acao": plano.get(
                "situacao_plano_acao"
            ),

            # ==========================================
            # EMENDA / PARLAMENTAR
            # ==========================================
            "nome_parlamentar": plano.get(
                "nome_parlamentar_emenda_plano_acao"
            ),

            "numero_emenda": plano.get(
                "numero_emenda_parlamentar_plano_acao"
            ),

            "codigo_emenda_formatado": plano.get(
                (
                    "codigo_emenda_parlamentar_"
                    "formatado_plano_acao"
                )
            ),

            # ==========================================
            # PROGRAMA
            # ==========================================
            "id_programa": plano.get(
                "id_programa"
            ),

            "codigo_programa": (
                programa.get(
                    "codigo_programa"
                )
                if programa
                else None
            ),

            "ano_programa": (
                programa.get(
                    "ano_programa"
                )
                if programa
                else None
            ),

            # ==========================================
            # BENEFICIÁRIO
            # ==========================================
            "id_beneficiario": plano.get(
                "id_beneficiario"
            ),

            "nome_beneficiario": (
                beneficiario.get(
                    "nome_beneficiario"
                )
                if beneficiario
                else None
            ),

            "cnpj_beneficiario": (
                beneficiario.get(
                    "cnpj_beneficiario"
                )
                if beneficiario
                else None
            ),

            "uf_beneficiario": (
                beneficiario.get(
                    "uf_beneficiario"
                )
                if beneficiario
                else None
            ),

            # ==========================================
            # OBJETO
            # ==========================================
            "nome_objeto": plano.get(
                "nome_objeto"
            ),

            "detalhamento_objeto": plano.get(
                "detalhamento_objeto"
            ),

            "categoria_despesa": plano.get(
                "categoria_despesa_plano_acao"
            ),

            # ==========================================
            # VALORES
            # ==========================================
            "valor_destinado": (
                valor_destinado
            ),

            "valor_custeio": plano.get(
                "valor_custeio_plano_acao"
            ),

            "valor_investimento": plano.get(
                "valor_investimento_plano_acao"
            ),

            "valor_transferido": (
                valor_transferido
            ),

            "origem_valor_transferido": (
                "OP_OB_FEDERAL"
            ),

            "valor_rendimentos": None,
            "recursos_disponiveis": None,

            "valor_empenhado": None,
            "valor_liquidado": None,
            "valor_pago": None,

            "valor_a_executar": None,
            "percentual_execucao": None,

            # ==========================================
            # CONTA
            # ==========================================
            "id_agencia_conta": (
                id_agencia_conta
            ),

            "conta_compartilhada": (
                conta_compartilhada
            ),

            "conta_exclusiva_te": (
                not conta_compartilhada
            ),

            "regra_conta": (
                "EXCLUSIVA_TE"
                if not conta_compartilhada
                else "COMPARTILHADA"
            ),

            "saldo_conta_te_confiavel": (
                saldo_confiavel_te
            ),

            "data_deposito": data_deposito,

            "saldo_conta": saldo_conta,

            "data_saldo": data_saldo,

            # ==========================================
            # PLANO DE TRABALHO
            # ==========================================
            "quantidade_planos_trabalho": len(
                planos_trabalho
            ),

            "situacoes_planos_trabalho": (
                self._situacoes_planos_trabalho(
                    planos_trabalho
                )
            ),

            "quantidade_planos_aprovados": sum(
                1
                for pt in planos_trabalho
                if self._normalizar_texto(
                    pt.get(
                        "situacao_plano_trabalho"
                    )
                )
                == "aprovado"
            ),

            "teve_complementacao": (
                teve_complementacao
            ),

            # ==========================================
            # METAS
            # ==========================================
            "quantidade_metas": len(
                metas
            ),

            # ==========================================
            # ANÁLISES
            # ==========================================
            "quantidade_analises": len(
                analises
            ),

            "quantidade_orgaos_analisadores": (
                quantidade_orgaos
            ),

            "multiplos_orgaos_analisadores": (
                quantidade_orgaos > 1
            ),

            # ==========================================
            # RELATÓRIOS
            # ==========================================
            "quantidade_relatorios_gestao": len(
                relatorios
            ),

            "tem_relatorio_gestao": bool(
                relatorios
            ),

            "tem_relatorio_novo": any(
                relatorio.get(
                    "origem_relatorio"
                )
                == "novos"
                for relatorio in relatorios
            ),

            "tem_relatorio_legado": any(
                relatorio.get(
                    "origem_relatorio"
                )
                == "legados"
                for relatorio in relatorios
            ),
        }

    # ==================================================
    # CONTA
    # ==================================================

    def _conta_compartilhada(
        self,
        id_agencia_conta: str | None,
        ano_plano_acao: int | None,
        planos_por_conta: dict[
            Any,
            list[Any],
        ],
    ) -> bool:
        """
        Regra de negócio:

        <= 2024:
            conta pode ser compartilhada.

        >= 2025:
            1 TE = 1 conta.

        O índice real também é consultado como
        verificação adicional.
        """

        if not id_agencia_conta:
            return False

        quantidade_planos = len(
            planos_por_conta.get(
                id_agencia_conta,
                [],
            )
        )

        if quantidade_planos > 1:
            return True

        if (
            ano_plano_acao is not None
            and ano_plano_acao
            < self.ANO_INICIO_CONTA_EXCLUSIVA
        ):
            return True

        return False

    # ==================================================
    # VALOR DESTINADO
    # ==================================================

    @staticmethod
    def _calcular_valor_destinado(
        plano: dict[str, Any],
    ) -> float:
        custeio = (
            plano.get(
                "valor_custeio_plano_acao"
            )
            or 0
        )

        investimento = (
            plano.get(
                "valor_investimento_plano_acao"
            )
            or 0
        )

        return float(
            custeio + investimento
        )

    # ==================================================
    # VALOR TRANSFERIDO
    # ==================================================

    @staticmethod
    def _calcular_valor_transferido_federal(
            empenhos: list[dict[str, Any]],
            dh_por_empenho: dict[Any, list[dict[str, Any]]],
            op_ob_por_dh: dict[Any, list[dict[str, Any]]],
        ) -> float:
            """
            Calcula o valor efetivamente transferido
            pela cadeia federal:

            Plano de Ação
                -> Empenho
                -> Documento Hábil
                -> OP/OB

            Considera o valor_dh somente quando existe
            pelo menos uma OP/OB vinculada ao documento hábil.
            """

            total = 0.0
            ids_dh_processados: set[Any] = set()

            for empenho in empenhos:
                id_empenho = empenho.get("id_empenho")

                if id_empenho is None:
                    continue

                documentos_habeis = dh_por_empenho.get(
                    id_empenho,
                    [],
                )

                for dh in documentos_habeis:
                    id_dh = dh.get("id_dh")

                    if id_dh is None:
                        continue

                    if id_dh in ids_dh_processados:
                        continue

                    movimentos = op_ob_por_dh.get(
                        id_dh,
                        [],
                    )

                    # Sem OP/OB não consideramos
                    # o valor como efetivamente transferido.
                    if not movimentos:
                        continue

                    valor_dh = dh.get("valor_dh")

                    if valor_dh is None:
                        continue

                    total += float(valor_dh)

                    ids_dh_processados.add(
                        id_dh
                    )

            return total

    # ==================================================
    # SALDO
    # ==================================================

    @staticmethod
    def _saldo_mais_recente(
        saldos: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not saldos:
            return None

        validos = [
            saldo
            for saldo in saldos
            if saldo.get(
                "data_saldo_conta"
            )
        ]

        if not validos:
            return saldos[0]

        return max(
            validos,
            key=lambda saldo: (
                saldo.get(
                    "data_saldo_conta"
                )
            ),
        )

    def _obter_saldo_mais_recente(
        self,
        saldos: list[dict[str, Any]],
    ) -> float | None:
        saldo = self._saldo_mais_recente(
            saldos
        )

        if saldo is None:
            return None

        valor = saldo.get(
            "saldo_final_gestao_financeira"
        )

        if valor is None:
            return None

        return float(valor)

    def _obter_data_saldo_mais_recente(
        self,
        saldos: list[dict[str, Any]],
    ) -> str | None:
        saldo = self._saldo_mais_recente(
            saldos
        )

        if saldo is None:
            return None

        return saldo.get(
            "data_saldo_conta"
        )

    # ==================================================
    # DATA DO DEPÓSITO
    # ==================================================

    @staticmethod
    def _obter_data_primeiro_deposito(
        lancamentos: list[dict[str, Any]],
    ) -> str | None:
        datas: list[str] = []

        for lancamento in lancamentos:
            tipo = str(
                lancamento.get(
                    "tipo_operacao_gestao_financeira"
                )
                or ""
            ).strip().upper()

            descricao = str(
                lancamento.get(
                    "descricao_gestao_financeira"
                )
                or ""
            ).strip().lower()

            data = lancamento.get(
                "data_lancamento_gestao_financeira"
            )

            if (
                tipo == "C"
                and "ordem banc" in descricao
                and data
            ):
                datas.append(data)

        if not datas:
            return None

        return min(datas)

    # ==================================================
    # PLANOS DE TRABALHO
    # ==================================================

    @staticmethod
    def _situacoes_planos_trabalho(
        planos_trabalho: list[dict[str, Any]],
    ) -> str | None:
        situacoes = sorted(
            {
                str(
                    plano.get(
                        "situacao_plano_trabalho"
                    )
                ).strip()
                for plano in planos_trabalho
                if plano.get(
                    "situacao_plano_trabalho"
                )
            }
        )

        if not situacoes:
            return None

        return " | ".join(
            situacoes
        )

    def _teve_complementacao(
        self,
        planos_trabalho: list[dict[str, Any]],
        analises: list[dict[str, Any]],
        historico_por_pt: dict[
            Any,
            list[dict[str, Any]],
        ],
    ) -> bool:
        for plano in planos_trabalho:
            id_plano_trabalho = plano.get(
                "id_plano_trabalho"
            )

            for evento in historico_por_pt.get(
                id_plano_trabalho,
                [],
            ):
                situacao = (
                    self._normalizar_texto(
                        evento.get(
                            "situacao_plano_trabalho_hist"
                        )
                    )
                )

                if "complement" in situacao:
                    return True

        for analise in analises:
            parecer = (
                self._normalizar_texto(
                    analise.get(
                        "situacao_parecer_analise_pt"
                    )
                )
            )

            if "complement" in parecer:
                return True

        return False

    # ==================================================
    # ANÁLISES
    # ==================================================

    @staticmethod
    def _quantidade_orgaos_analisadores(
        analises: list[dict[str, Any]],
    ) -> int:
        orgaos = {
            (
                analise.get(
                    "codigo_siorg_orgao_analise_pt"
                )
                or analise.get(
                    "nome_orgao_analise_pt"
                )
            )
            for analise in analises
            if (
                analise.get(
                    "codigo_siorg_orgao_analise_pt"
                )
                is not None
                or analise.get(
                    "nome_orgao_analise_pt"
                )
            )
        }

        return len(orgaos)

    # ==================================================
    # UTILITÁRIOS
    # ==================================================

    @staticmethod
    def _normalizar_texto(
        valor: Any,
    ) -> str:
        if valor is None:
            return ""

        return str(
            valor
        ).strip().lower()
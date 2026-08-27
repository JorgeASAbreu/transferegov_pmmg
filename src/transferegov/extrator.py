from __future__ import annotations

from typing import Any, Callable

from .api import TransferegovAPI
from .config import CNPJ_PMMG
from .logger import configurar_logger


class ExtratorPMMG:
    def __init__(self) -> None:
        self.api = TransferegovAPI()

        self.logger = configurar_logger(
            "transferegov.extrator"
        )

    # ==================================================
    # EXECUTOR
    # ==================================================

    def buscar_executores(
        self,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "executores_especiais",
            filtros={
                "cnpj_executor": CNPJ_PMMG,
            },
        )

    def buscar_finalidades(
        self,
        id_executor: int,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "finalidade_especiais",
            filtros={
                "id_executor": id_executor,
            },
        )

    # ==================================================
    # PLANO DE AÇÃO
    # ==================================================

    def buscar_plano_acao(
        self,
        id_plano_acao: int,
    ) -> dict | None:
        dados = self.api.consultar_paginado(
            "planos_acao_especiais",
            filtros={
                "id_plano_acao": id_plano_acao,
            },
        )

        if not dados:
            return None

        return dados[0]

    def buscar_historico_plano_acao(
        self,
        id_plano_acao: int,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "planos_acao_historico_especiais",
            filtros={
                "id_plano_acao": id_plano_acao,
            },
        )

    # ==================================================
    # BENEFICIÁRIO
    # ==================================================

    def buscar_beneficiario(
        self,
        id_beneficiario: int,
    ) -> dict | None:
        dados = self.api.consultar_paginado(
            "beneficiarios_especiais",
            filtros={
                "id_beneficiario": id_beneficiario,
            },
        )

        if not dados:
            return None

        return dados[0]

    # ==================================================
    # PROGRAMA
    # ==================================================

    def buscar_programa(
        self,
        id_programa: int,
    ) -> dict | None:
        dados = self.api.consultar_paginado(
            "programas_especiais",
            filtros={
                "id_programa": id_programa,
            },
        )

        if not dados:
            return None

        return dados[0]

    # ==================================================
    # PLANO DE TRABALHO
    # ==================================================

    def buscar_planos_trabalho(
        self,
        id_plano_acao: int,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "planos_trabalho_especiais",
            filtros={
                "id_plano_acao": id_plano_acao,
            },
        )

    def buscar_historico_plano_trabalho(
        self,
        id_plano_trabalho: int,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "planos_trabalho_historico",
            filtros={
                "id_plano_trabalho": id_plano_trabalho,
            },
        )

    # ==================================================
    # METAS
    # ==================================================

    def buscar_metas(
        self,
        id_executor: int,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "meta_especiais",
            filtros={
                "id_executor": id_executor,
            },
        )

    # ==================================================
    # EXECUÇÃO FINANCEIRA FEDERAL
    # ==================================================

    def buscar_empenhos(
        self,
        id_plano_acao: int,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "empenhos_especiais",
            filtros={
                "id_plano_acao": id_plano_acao,
            },
        )

    def buscar_documentos_habeis(
        self,
        id_empenho: int,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "documentos_habeis_especiais",
            filtros={
                "id_empenho": id_empenho,
            },
        )

    def buscar_op_ob(
        self,
        id_dh: int,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            (
                "ordens_pagamentos_"
                "ordens_bancarias_especiais"
            ),
            filtros={
                "id_dh": id_dh,
            },
        )

    # ==================================================
    # GESTÃO FINANCEIRA
    # ==================================================

    def buscar_lancamentos_gestao_financeira(
        self,
        id_agencia_conta: str,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "gestao_financeira_lancamentos_especiais",
            filtros={
                "id_agencia_conta": id_agencia_conta,
            },
        )

    def buscar_subtransacoes_gestao_financeira(
        self,
        id_lancamento_gestao_financeira: str,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "gestao_financeira_subtransacoes_especiais",
            filtros={
                "id_lancamento_gestao_financeira": (
                    id_lancamento_gestao_financeira
                ),
            },
        )

    def buscar_saldo_gestao_financeira(
        self,
        id_agencia_conta: str,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "saldo_conta_gestao_financeira_especiais",
            filtros={
                "id_agencia_conta": id_agencia_conta,
            },
        )

    # ==================================================
    # RELATÓRIOS DE GESTÃO
    # ==================================================

    def buscar_relatorios_gestao_novos(
        self,
        id_plano_acao: int,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "relatorios_gestao_novos_especiais",
            filtros={
                "id_plano_acao": id_plano_acao,
            },
        )

    def buscar_relatorios_gestao_legados(
        self,
        id_plano_acao: int,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "relatorios_gestao_especiais",
            filtros={
                "id_plano_acao": id_plano_acao,
            },
        )

    # ==================================================
    # ANÁLISES
    # ==================================================

    def buscar_analises_plano_trabalho(
        self,
        id_plano_trabalho: int,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "planos_trabalho_analises_especiais",
            filtros={
                "id_plano_trabalho": id_plano_trabalho,
            },
        )

    def buscar_historico_analise(
        self,
        id_plano_trabalho_analise_pt: int,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            (
                "plano_trabalho_analise_"
                "historico_especiais"
            ),
            filtros={
                "id_plano_trabalho_analise_pt": (
                    id_plano_trabalho_analise_pt
                ),
            },
        )

    def buscar_orgaos_analises_pendentes(
        self,
        id_plano_trabalho: int,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "orgaos_analises_pendentes_especiais",
            filtros={
                "id_plano_trabalho": id_plano_trabalho,
            },
        )

    # ==================================================
    # CONTROLE DE FALHAS
    # ==================================================

    def executar_etapa(
        self,
        nome_etapa: str,
        funcao: Callable[..., Any],
        *args: Any,
        valor_padrao: Any = None,
    ) -> tuple[Any, dict | None]:
        """
        Executa uma etapa isoladamente.

        Uma falha em um endpoint secundário não
        interrompe a extração completa do plano.
        """

        try:
            resultado = funcao(*args)

            self.logger.info(
                "Etapa concluída | etapa=%s",
                nome_etapa,
            )

            return resultado, None

        except Exception as erro:
            self.logger.error(
                (
                    "Falha parcial | "
                    "etapa=%s | "
                    "erro=%s"
                ),
                nome_etapa,
                erro,
            )

            return (
                valor_padrao,
                {
                    "etapa": nome_etapa,
                    "erro": str(erro),
                },
            )

    # ==================================================
    # ENRIQUECIMENTO - EXECUTOR
    # ==================================================

    def enriquecer_executor(
        self,
        executor: dict,
        erros: list[dict],
    ) -> dict:
        executor_enriquecido = dict(executor)

        id_executor = executor.get(
            "id_executor"
        )

        if id_executor is None:
            executor_enriquecido[
                "finalidades"
            ] = []

            return executor_enriquecido

        finalidades, falha = (
            self.executar_etapa(
                "finalidades",
                self.buscar_finalidades,
                id_executor,
                valor_padrao=[],
            )
        )

        if falha:
            falha[
                "id_executor"
            ] = id_executor

            erros.append(falha)

        executor_enriquecido[
            "finalidades"
        ] = finalidades

        return executor_enriquecido

    # ==================================================
    # ENRIQUECIMENTO - PLANO DE AÇÃO
    # ==================================================

    def enriquecer_plano_acao(
        self,
        plano_acao: dict | None,
        erros: list[dict],
    ) -> dict | None:
        if plano_acao is None:
            return None

        plano_enriquecido = dict(
            plano_acao
        )

        id_plano_acao = plano_acao.get(
            "id_plano_acao"
        )

        # ----------------------------------------------
        # Histórico do Plano de Ação
        # ----------------------------------------------

        if id_plano_acao is not None:
            historico, falha = (
                self.executar_etapa(
                    "historico_plano_acao",
                    self.buscar_historico_plano_acao,
                    id_plano_acao,
                    valor_padrao=[],
                )
            )

            if falha:
                falha[
                    "id_plano_acao"
                ] = id_plano_acao

                erros.append(falha)

            plano_enriquecido[
                "historico"
            ] = historico

        else:
            plano_enriquecido[
                "historico"
            ] = []

        # ----------------------------------------------
        # Beneficiário
        # ----------------------------------------------

        id_beneficiario = plano_acao.get(
            "id_beneficiario"
        )

        if id_beneficiario is not None:
            beneficiario, falha = (
                self.executar_etapa(
                    "beneficiario",
                    self.buscar_beneficiario,
                    id_beneficiario,
                    valor_padrao=None,
                )
            )

            if falha:
                falha[
                    "id_beneficiario"
                ] = id_beneficiario

                erros.append(falha)

            plano_enriquecido[
                "beneficiario"
            ] = beneficiario

        else:
            plano_enriquecido[
                "beneficiario"
            ] = None

        # ----------------------------------------------
        # Programa
        # ----------------------------------------------

        id_programa = plano_acao.get(
            "id_programa"
        )

        if id_programa is not None:
            programa, falha = (
                self.executar_etapa(
                    "programa",
                    self.buscar_programa,
                    id_programa,
                    valor_padrao=None,
                )
            )

            if falha:
                falha[
                    "id_programa"
                ] = id_programa

                erros.append(falha)

            plano_enriquecido[
                "programa"
            ] = programa

        else:
            plano_enriquecido[
                "programa"
            ] = None

        return plano_enriquecido

    # ==================================================
    # ENRIQUECIMENTO - DOCUMENTOS HÁBEIS
    # ==================================================

    def enriquecer_documentos_habeis(
        self,
        documentos_habeis: list[dict],
        erros: list[dict],
    ) -> list[dict]:
        for documento in documentos_habeis:
            id_dh = documento.get(
                "id_dh"
            )

            if id_dh is None:
                documento["op_ob"] = []

                erros.append(
                    {
                        "etapa": "op_ob",
                        "erro": (
                            "Documento hábil sem id_dh."
                        ),
                    }
                )

                self.logger.warning(
                    "Documento hábil sem id_dh"
                )

                continue

            op_ob, falha = (
                self.executar_etapa(
                    "op_ob",
                    self.buscar_op_ob,
                    id_dh,
                    valor_padrao=[],
                )
            )

            documento["op_ob"] = op_ob

            if falha:
                falha["id_dh"] = id_dh
                erros.append(falha)

        return documentos_habeis

    # ==================================================
    # ENRIQUECIMENTO - EMPENHOS
    # ==================================================

    def enriquecer_empenhos(
        self,
        empenhos: list[dict],
        erros: list[dict],
    ) -> list[dict]:
        for empenho in empenhos:
            id_empenho = empenho.get(
                "id_empenho"
            )

            if id_empenho is None:
                empenho[
                    "documentos_habeis"
                ] = []

                erros.append(
                    {
                        "etapa": (
                            "documentos_habeis"
                        ),
                        "erro": (
                            "Empenho sem id_empenho."
                        ),
                    }
                )

                self.logger.warning(
                    "Empenho sem id_empenho"
                )

                continue

            documentos_habeis, falha = (
                self.executar_etapa(
                    "documentos_habeis",
                    self.buscar_documentos_habeis,
                    id_empenho,
                    valor_padrao=[],
                )
            )

            if falha:
                falha[
                    "id_empenho"
                ] = id_empenho

                erros.append(falha)

            empenho[
                "documentos_habeis"
            ] = (
                self
                .enriquecer_documentos_habeis(
                    documentos_habeis,
                    erros,
                )
            )

        return empenhos

    # ==================================================
    # ENRIQUECIMENTO - GESTÃO FINANCEIRA
    # ==================================================

    def enriquecer_lancamentos_gestao_financeira(
        self,
        lancamentos: list[dict],
        erros: list[dict],
    ) -> list[dict]:
        for lancamento in lancamentos:
            quantidade = lancamento.get(
                (
                    "quantidade_subtransacoes_"
                    "lancamento_gestao_financeira"
                ),
                0,
            )

            if not quantidade:
                lancamento[
                    "subtransacoes"
                ] = []

                continue

            id_lancamento = lancamento.get(
                "id_lancamento_gestao_financeira"
            )

            if not id_lancamento:
                lancamento[
                    "subtransacoes"
                ] = []

                erros.append(
                    {
                        "etapa": (
                            "subtransacoes_"
                            "gestao_financeira"
                        ),
                        "erro": (
                            "Lançamento com "
                            "subtransações sem "
                            "identificador."
                        ),
                    }
                )

                continue

            subtransacoes, falha = (
                self.executar_etapa(
                    (
                        "subtransacoes_"
                        "gestao_financeira"
                    ),
                    (
                        self
                        .buscar_subtransacoes_gestao_financeira
                    ),
                    id_lancamento,
                    valor_padrao=[],
                )
            )

            lancamento[
                "subtransacoes"
            ] = subtransacoes

            if falha:
                falha[
                    "id_lancamento_gestao_financeira"
                ] = id_lancamento

                erros.append(falha)

        return lancamentos

    def enriquecer_gestao_financeira(
        self,
        plano_acao: dict | None,
        erros: list[dict],
    ) -> dict:
        resultado = {
            "id_agencia_conta": None,
            "lancamentos": [],
            "saldo_conta": [],
        }

        if plano_acao is None:
            return resultado

        id_agencia_conta = plano_acao.get(
            "id_agencia_conta"
        )

        resultado[
            "id_agencia_conta"
        ] = id_agencia_conta

        if not id_agencia_conta:
            return resultado

        lancamentos, falha = (
            self.executar_etapa(
                "lancamentos_gestao_financeira",
                self.buscar_lancamentos_gestao_financeira,
                id_agencia_conta,
                valor_padrao=[],
            )
        )

        if falha:
            falha[
                "id_agencia_conta"
            ] = id_agencia_conta

            erros.append(falha)

        lancamentos = (
            self.enriquecer_lancamentos_gestao_financeira(
                lancamentos,
                erros,
            )
        )

        saldo_conta, falha = (
            self.executar_etapa(
                "saldo_gestao_financeira",
                self.buscar_saldo_gestao_financeira,
                id_agencia_conta,
                valor_padrao=[],
            )
        )

        if falha:
            falha[
                "id_agencia_conta"
            ] = id_agencia_conta

            erros.append(falha)

        resultado[
            "lancamentos"
        ] = lancamentos

        resultado[
            "saldo_conta"
        ] = saldo_conta

        return resultado

    # ==================================================
    # ENRIQUECIMENTO - RELATÓRIOS DE GESTÃO
    # ==================================================

    def enriquecer_relatorios_gestao(
        self,
        id_plano_acao: int,
        erros: list[dict],
    ) -> dict:
        resultado = {
            "novos": [],
            "legados": [],
        }

        novos, falha = (
            self.executar_etapa(
                "relatorios_gestao_novos",
                self.buscar_relatorios_gestao_novos,
                id_plano_acao,
                valor_padrao=[],
            )
        )

        if falha:
            falha[
                "id_plano_acao"
            ] = id_plano_acao

            erros.append(falha)

        legados, falha = (
            self.executar_etapa(
                "relatorios_gestao_legados",
                self.buscar_relatorios_gestao_legados,
                id_plano_acao,
                valor_padrao=[],
            )
        )

        if falha:
            falha[
                "id_plano_acao"
            ] = id_plano_acao

            erros.append(falha)

        resultado["novos"] = novos
        resultado["legados"] = legados

        return resultado

    # ==================================================
    # ENRIQUECIMENTO - ANÁLISES
    # ==================================================

    def enriquecer_analises(
        self,
        analises: list[dict],
        erros: list[dict],
    ) -> list[dict]:
        for analise in analises:
            id_analise = analise.get(
                "id_plano_trabalho_analise_pt"
            )

            if id_analise is None:
                analise[
                    "historico"
                ] = []

                erros.append(
                    {
                        "etapa": (
                            "historico_analise"
                        ),
                        "erro": (
                            "Análise sem "
                            "identificador."
                        ),
                    }
                )

                continue

            historico, falha = (
                self.executar_etapa(
                    "historico_analise",
                    self.buscar_historico_analise,
                    id_analise,
                    valor_padrao=[],
                )
            )

            analise[
                "historico"
            ] = historico

            if falha:
                falha[
                    "id_plano_trabalho_analise_pt"
                ] = id_analise

                erros.append(falha)

        return analises

    # ==================================================
    # ENRIQUECIMENTO - PLANOS DE TRABALHO
    # ==================================================

    def enriquecer_planos_trabalho(
        self,
        planos_trabalho: list[dict],
        erros: list[dict],
    ) -> list[dict]:
        for plano_trabalho in planos_trabalho:
            id_plano_trabalho = (
                plano_trabalho.get(
                    "id_plano_trabalho"
                )
            )

            plano_trabalho[
                "historico"
            ] = []

            plano_trabalho[
                "analises"
            ] = []

            plano_trabalho[
                "orgaos_analises_pendentes"
            ] = []

            if id_plano_trabalho is None:
                erros.append(
                    {
                        "etapa": (
                            "enriquecimento_"
                            "plano_trabalho"
                        ),
                        "erro": (
                            "Plano de trabalho "
                            "sem id_plano_trabalho."
                        ),
                    }
                )

                continue

            # ------------------------------------------
            # Histórico do plano de trabalho
            # ------------------------------------------

            historico, falha = (
                self.executar_etapa(
                    "historico_plano_trabalho",
                    self.buscar_historico_plano_trabalho,
                    id_plano_trabalho,
                    valor_padrao=[],
                )
            )

            if falha:
                falha[
                    "id_plano_trabalho"
                ] = id_plano_trabalho

                erros.append(falha)

            plano_trabalho[
                "historico"
            ] = historico

            # ------------------------------------------
            # Análises
            # ------------------------------------------

            analises, falha = (
                self.executar_etapa(
                    "analises_plano_trabalho",
                    self.buscar_analises_plano_trabalho,
                    id_plano_trabalho,
                    valor_padrao=[],
                )
            )

            if falha:
                falha[
                    "id_plano_trabalho"
                ] = id_plano_trabalho

                erros.append(falha)

            plano_trabalho[
                "analises"
            ] = self.enriquecer_analises(
                analises,
                erros,
            )

            # ------------------------------------------
            # Órgãos com análise pendente
            # ------------------------------------------

            pendentes, falha = (
                self.executar_etapa(
                    "orgaos_analises_pendentes",
                    self.buscar_orgaos_analises_pendentes,
                    id_plano_trabalho,
                    valor_padrao=[],
                )
            )

            if falha:
                falha[
                    "id_plano_trabalho"
                ] = id_plano_trabalho

                erros.append(falha)

            plano_trabalho[
                "orgaos_analises_pendentes"
            ] = pendentes

        return planos_trabalho

    # ==================================================
    # EXTRAÇÃO DE UM PLANO
    # ==================================================

    def extrair_plano(
        self,
        executor: dict,
    ) -> dict:
        id_executor = executor[
            "id_executor"
        ]

        id_plano_acao = executor[
            "id_plano_acao"
        ]

        erros: list[dict] = []

        self.logger.info(
            (
                "Iniciando plano | "
                "plano=%s | "
                "executor=%s"
            ),
            id_plano_acao,
            id_executor,
        )

        # ----------------------------------------------
        # Executor + Finalidades
        # ----------------------------------------------

        executor_enriquecido = (
            self.enriquecer_executor(
                executor,
                erros,
            )
        )

        # ----------------------------------------------
        # Plano de Ação
        # ----------------------------------------------

        plano_acao, falha = (
            self.executar_etapa(
                "plano_acao",
                self.buscar_plano_acao,
                id_plano_acao,
                valor_padrao=None,
            )
        )

        if falha:
            falha[
                "id_plano_acao"
            ] = id_plano_acao

            erros.append(falha)

        plano_acao_enriquecido = (
            self.enriquecer_plano_acao(
                plano_acao,
                erros,
            )
        )

        # ----------------------------------------------
        # Planos de Trabalho
        # ----------------------------------------------

        planos_trabalho, falha = (
            self.executar_etapa(
                "planos_trabalho",
                self.buscar_planos_trabalho,
                id_plano_acao,
                valor_padrao=[],
            )
        )

        if falha:
            falha[
                "id_plano_acao"
            ] = id_plano_acao

            erros.append(falha)

        planos_trabalho = (
            self.enriquecer_planos_trabalho(
                planos_trabalho,
                erros,
            )
        )

        # ----------------------------------------------
        # Metas
        # ----------------------------------------------

        metas, falha = (
            self.executar_etapa(
                "metas",
                self.buscar_metas,
                id_executor,
                valor_padrao=[],
            )
        )

        if falha:
            falha[
                "id_executor"
            ] = id_executor

            erros.append(falha)

        # ----------------------------------------------
        # Execução financeira
        # ----------------------------------------------

        empenhos, falha = (
            self.executar_etapa(
                "empenhos",
                self.buscar_empenhos,
                id_plano_acao,
                valor_padrao=[],
            )
        )

        if falha:
            falha[
                "id_plano_acao"
            ] = id_plano_acao

            erros.append(falha)

        empenhos = (
            self.enriquecer_empenhos(
                empenhos,
                erros,
            )
        )

        # ----------------------------------------------
        # Gestão financeira
        # ----------------------------------------------

        gestao_financeira = (
            self.enriquecer_gestao_financeira(
                plano_acao,
                erros,
            )
        )

        # ----------------------------------------------
        # Relatórios de Gestão
        # ----------------------------------------------

        relatorios_gestao = (
            self.enriquecer_relatorios_gestao(
                id_plano_acao,
                erros,
            )
        )

        # ----------------------------------------------
        # Status
        # ----------------------------------------------

        status_extracao = (
            "COM_ERROS"
            if erros
            else "OK"
        )

        if status_extracao == "OK":
            self.logger.info(
                (
                    "Plano concluído | "
                    "plano=%s | "
                    "executor=%s | "
                    "status=OK"
                ),
                id_plano_acao,
                id_executor,
            )

        else:
            self.logger.warning(
                (
                    "Plano concluído | "
                    "plano=%s | "
                    "executor=%s | "
                    "status=COM_ERROS | "
                    "erros=%s"
                ),
                id_plano_acao,
                id_executor,
                len(erros),
            )

        return {
            "executor": (
                executor_enriquecido
            ),
            "plano_acao": (
                plano_acao_enriquecido
            ),
            "planos_trabalho": (
                planos_trabalho
            ),
            "metas": metas,
            "empenhos": empenhos,
            "gestao_financeira": (
                gestao_financeira
            ),
            "relatorios_gestao": (
                relatorios_gestao
            ),
            "status_extracao": (
                status_extracao
            ),
            "erros_extracao": erros,
        }

    # ==================================================
    # EXTRAÇÃO COMPLETA
    # ==================================================

    def extrair(
        self,
    ) -> list[dict]:
        self.logger.info(
            "Buscando executores da PMMG"
        )

        executores = (
            self.buscar_executores()
        )

        total = len(executores)

        self.logger.info(
            "Executores encontrados=%s",
            total,
        )

        resultados: list[dict] = []

        for indice, executor in enumerate(
            executores,
            start=1,
        ):
            id_executor = executor[
                "id_executor"
            ]

            id_plano_acao = executor[
                "id_plano_acao"
            ]

            self.logger.info(
                (
                    "Processando | "
                    "%s/%s | "
                    "plano=%s | "
                    "executor=%s"
                ),
                indice,
                total,
                id_plano_acao,
                id_executor,
            )

            resultado = (
                self.extrair_plano(
                    executor
                )
            )

            resultados.append(
                resultado
            )

        return resultados
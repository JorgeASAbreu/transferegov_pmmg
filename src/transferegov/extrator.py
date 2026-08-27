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
                "id_plano_trabalho": (
                    id_plano_trabalho
                ),
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
                "id_plano_trabalho": (
                    id_plano_trabalho
                ),
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
        Executa uma etapa de forma isolada.

        Em caso de erro:
        - registra a falha no log;
        - retorna o valor padrão;
        - preserva os demais dados do plano.
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

            falha = {
                "etapa": nome_etapa,
                "erro": str(erro),
            }

            return valor_padrao, falha

    # ==================================================
    # ENRIQUECIMENTO - DOCUMENTOS HÁBEIS
    # ==================================================

    def enriquecer_documentos_habeis(
        self,
        documentos_habeis: list[dict],
        erros: list[dict],
    ) -> list[dict]:
        for documento in documentos_habeis:
            id_dh = documento.get("id_dh")

            if id_dh is None:
                documento["op_ob"] = []

                falha = {
                    "etapa": "op_ob",
                    "erro": (
                        "Documento hábil sem id_dh."
                    ),
                }

                erros.append(falha)

                self.logger.warning(
                    "Documento hábil sem id_dh"
                )

                continue

            op_ob, falha = self.executar_etapa(
                "op_ob",
                self.buscar_op_ob,
                id_dh,
                valor_padrao=[],
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

                falha = {
                    "etapa": (
                        "documentos_habeis"
                    ),
                    "erro": (
                        "Empenho sem id_empenho."
                    ),
                }

                erros.append(falha)

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

            documentos_habeis = (
                self.enriquecer_documentos_habeis(
                    documentos_habeis,
                    erros,
                )
            )

            empenho[
                "documentos_habeis"
            ] = documentos_habeis

        return empenhos

    # ==================================================
    # ENRIQUECIMENTO - SUBTRANSAÇÕES
    # ==================================================

    def enriquecer_lancamentos_gestao_financeira(
        self,
        lancamentos: list[dict],
        erros: list[dict],
    ) -> list[dict]:
        """
        Consulta subtransações apenas quando
        a API informar quantidade maior que zero.
        """

        for lancamento in lancamentos:
            quantidade = lancamento.get(
                (
                    "quantidade_subtransacoes_"
                    "lancamento_gestao_financeira"
                ),
                0,
            )

            if not quantidade:
                lancamento["subtransacoes"] = []
                continue

            id_lancamento = lancamento.get(
                "id_lancamento_gestao_financeira"
            )

            if not id_lancamento:
                lancamento["subtransacoes"] = []

                falha = {
                    "etapa": (
                        "subtransacoes_"
                        "gestao_financeira"
                    ),
                    "erro": (
                        "Lançamento com subtransações "
                        "sem identificador."
                    ),
                }

                erros.append(falha)

                self.logger.warning(
                    (
                        "Lançamento com subtransações "
                        "sem identificador"
                    )
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

    # ==================================================
    # ENRIQUECIMENTO - GESTÃO FINANCEIRA
    # ==================================================

    def enriquecer_gestao_financeira(
        self,
        plano_acao: dict | None,
        erros: list[dict],
    ) -> dict:
        gestao_financeira = {
            "id_agencia_conta": None,
            "lancamentos": [],
            "saldo_conta": [],
        }

        if not plano_acao:
            self.logger.warning(
                (
                    "Gestão financeira ignorada: "
                    "plano_acao indisponível"
                )
            )

            return gestao_financeira

        id_agencia_conta = plano_acao.get(
            "id_agencia_conta"
        )

        gestao_financeira[
            "id_agencia_conta"
        ] = id_agencia_conta

        if not id_agencia_conta:
            self.logger.info(
                (
                    "Gestão financeira sem consulta: "
                    "plano sem id_agencia_conta"
                )
            )

            return gestao_financeira

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

        gestao_financeira[
            "lancamentos"
        ] = lancamentos

        gestao_financeira[
            "saldo_conta"
        ] = saldo_conta

        return gestao_financeira

    # ==================================================
    # ENRIQUECIMENTO - RELATÓRIOS DE GESTÃO
    # ==================================================

    def enriquecer_relatorios_gestao(
        self,
        id_plano_acao: int,
        erros: list[dict],
    ) -> dict:
        relatorios = {
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

        relatorios["novos"] = novos
        relatorios["legados"] = legados

        return relatorios

    # ==================================================
    # ENRIQUECIMENTO - HISTÓRICO DAS ANÁLISES
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
                analise["historico"] = []

                falha = {
                    "etapa": (
                        "historico_analise"
                    ),
                    "erro": (
                        "Análise sem "
                        "id_plano_trabalho_analise_pt."
                    ),
                }

                erros.append(falha)

                self.logger.warning(
                    "Análise sem identificador"
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
        """
        Acrescenta a cada Plano de Trabalho:

        - analises[]
          - historico[]
        - orgaos_analises_pendentes[]
        """

        for plano_trabalho in planos_trabalho:
            id_plano_trabalho = (
                plano_trabalho.get(
                    "id_plano_trabalho"
                )
            )

            if id_plano_trabalho is None:
                plano_trabalho[
                    "analises"
                ] = []

                plano_trabalho[
                    "orgaos_analises_pendentes"
                ] = []

                falha = {
                    "etapa": (
                        "analises_plano_trabalho"
                    ),
                    "erro": (
                        "Plano de trabalho sem "
                        "id_plano_trabalho."
                    ),
                }

                erros.append(falha)

                self.logger.warning(
                    (
                        "Plano de trabalho "
                        "sem identificador"
                    )
                )

                continue

            # ------------------------------------------
            # Análises atuais
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

            analises = self.enriquecer_analises(
                analises,
                erros,
            )

            plano_trabalho[
                "analises"
            ] = analises

            # ------------------------------------------
            # Órgãos pendentes
            # ------------------------------------------

            pendentes, falha = (
                self.executar_etapa(
                    (
                        "orgaos_analises_"
                        "pendentes"
                    ),
                    (
                        self
                        .buscar_orgaos_analises_pendentes
                    ),
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
        # Empenhos
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

        empenhos = self.enriquecer_empenhos(
            empenhos,
            erros,
        )

        # ----------------------------------------------
        # Gestão Financeira
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
            "executor": executor,
            "plano_acao": plano_acao,
            "planos_trabalho": planos_trabalho,
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

        executores = self.buscar_executores()

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

            resultado = self.extrair_plano(
                executor
            )

            resultados.append(resultado)

        return resultados
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

    # --------------------------------------------------
    # CONSULTAS
    # --------------------------------------------------

    def buscar_executores(
        self,
    ) -> list[dict]:
        return self.api.consultar_paginado(
            "executores_especiais",
            filtros={
                "cnpj_executor": CNPJ_PMMG,
            },
        )

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

    # --------------------------------------------------
    # CONTROLE DE FALHAS
    # --------------------------------------------------

    def executar_etapa(
        self,
        nome_etapa: str,
        funcao: Callable[..., Any],
        *args: Any,
        valor_padrao: Any = None,
    ) -> tuple[Any, dict | None]:
        """
        Executa uma etapa isoladamente.

        Se ocorrer erro, registra a falha e retorna
        um valor padrão sem interromper todo o plano.
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

    # --------------------------------------------------
    # ENRIQUECIMENTO FINANCEIRO
    # --------------------------------------------------

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

    # --------------------------------------------------
    # EXTRAÇÃO DE UM PLANO
    # --------------------------------------------------

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
            "status_extracao": status_extracao,
            "erros_extracao": erros,
        }

    # --------------------------------------------------
    # EXTRAÇÃO COMPLETA
    # --------------------------------------------------

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
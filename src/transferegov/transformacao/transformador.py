from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TransformadorTransferegov:
    def __init__(
        self,
        caminho_json: str = "dados/transferegov_pmmg.json",
    ) -> None:
        self.caminho_json = Path(caminho_json)

    def carregar_dados(
        self,
    ) -> list[dict[str, Any]]:
        if not self.caminho_json.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {self.caminho_json}"
            )

        with self.caminho_json.open(
            "r",
            encoding="utf-8",
        ) as arquivo:
            dados = json.load(arquivo)

        if not isinstance(dados, list):
            raise ValueError(
                "O JSON principal deve conter uma lista de registros."
            )

        return dados

    def normalizar(
        self,
    ) -> dict[str, list[dict[str, Any]]]:
        dados = self.carregar_dados()

        tabelas: dict[str, list[dict[str, Any]]] = {
            "executores": [],
            "finalidades": [],
            "planos_acao": [],
            "historico_planos_acao": [],
            "beneficiarios": [],
            "programas": [],
            "planos_trabalho": [],
            "historico_planos_trabalho": [],
            "metas": [],
            "analises": [],
            "historico_analises": [],
            "orgaos_analises_pendentes": [],
            "relatorios_gestao": [],
            "empenhos": [],
            "documentos_habeis": [],
            "op_ob": [],
            "lancamentos_financeiros": [],
            "subtransacoes_financeiras": [],
            "saldos_conta": [],
        }

        for registro in dados:
            self._normalizar_registro(
                registro,
                tabelas,
            )

        return tabelas

    def _normalizar_registro(
        self,
        registro: dict[str, Any],
        tabelas: dict[str, list[dict[str, Any]]],
    ) -> None:
        executor = registro.get("executor") or {}
        plano_acao = registro.get("plano_acao") or {}

        id_executor = executor.get("id_executor")
        id_plano_acao = plano_acao.get("id_plano_acao")

        self._normalizar_executor(
            executor,
            tabelas,
        )

        self._normalizar_plano_acao(
            plano_acao,
            tabelas,
        )

        self._normalizar_planos_trabalho(
            registro.get("planos_trabalho") or [],
            id_plano_acao,
            tabelas,
        )

        self._normalizar_metas(
            registro.get("metas") or [],
            id_plano_acao,
            id_executor,
            tabelas,
        )

        self._normalizar_empenhos(
            registro.get("empenhos") or [],
            id_plano_acao,
            tabelas,
        )

        self._normalizar_gestao_financeira(
            registro.get("gestao_financeira") or {},
            id_plano_acao,
            tabelas,
        )

        self._normalizar_relatorios_gestao(
            registro.get("relatorios_gestao") or {},
            id_plano_acao,
            tabelas,
        )

    def _normalizar_executor(
        self,
        executor: dict[str, Any],
        tabelas: dict[str, list[dict[str, Any]]],
    ) -> None:
        if not executor:
            return

        finalidades = executor.get("finalidades") or []

        executor_limpo = {
            chave: valor
            for chave, valor in executor.items()
            if chave != "finalidades"
        }

        self._adicionar_unico(
            tabelas["executores"],
            executor_limpo,
            "id_executor",
        )

        for finalidade in finalidades:
            self._adicionar_unico_composto(
                tabelas["finalidades"],
                finalidade,
                [
                    "id_executor",
                    "cd_area_politica_publica_tipo_pt",
                    "cd_area_politica_publica_pt",
                ],
            )

    def _normalizar_plano_acao(
        self,
        plano_acao: dict[str, Any],
        tabelas: dict[str, list[dict[str, Any]]],
    ) -> None:
        if not plano_acao:
            return

        historico = plano_acao.get("historico") or []
        beneficiario = plano_acao.get("beneficiario")
        programa = plano_acao.get("programa")

        plano_limpo = {
            chave: valor
            for chave, valor in plano_acao.items()
            if chave not in {
                "historico",
                "beneficiario",
                "programa",
            }
        }

        self._adicionar_unico(
            tabelas["planos_acao"],
            plano_limpo,
            "id_plano_acao",
        )

        for evento in historico:
            self._adicionar_unico(
                tabelas["historico_planos_acao"],
                evento,
                "id_historico_plano_acao",
            )

        if beneficiario:
            self._adicionar_unico(
                tabelas["beneficiarios"],
                beneficiario,
                "id_beneficiario",
            )

        if programa:
            self._adicionar_unico(
                tabelas["programas"],
                programa,
                "id_programa",
            )

    def _normalizar_planos_trabalho(
        self,
        planos_trabalho: list[dict[str, Any]],
        id_plano_acao: int | None,
        tabelas: dict[str, list[dict[str, Any]]],
    ) -> None:
        for plano_trabalho in planos_trabalho:
            historico = plano_trabalho.get("historico") or []
            analises = plano_trabalho.get("analises") or []
            pendentes = (
                plano_trabalho.get(
                    "orgaos_analises_pendentes"
                )
                or []
            )

            plano_limpo = {
                chave: valor
                for chave, valor in plano_trabalho.items()
                if chave not in {
                    "historico",
                    "analises",
                    "orgaos_analises_pendentes",
                }
            }

            plano_limpo.setdefault(
                "id_plano_acao",
                id_plano_acao,
            )

            self._adicionar_unico(
                tabelas["planos_trabalho"],
                plano_limpo,
                "id_plano_trabalho",
            )

            for evento in historico:
                self._adicionar_unico(
                    tabelas["historico_planos_trabalho"],
                    evento,
                    "id_plano_trabalho_hist",
                )

            for analise in analises:
                self._normalizar_analise(
                    analise,
                    id_plano_acao,
                    tabelas,
                )

            for pendente in pendentes:
                linha = dict(pendente)

                linha.setdefault(
                    "id_plano_trabalho",
                    plano_trabalho.get(
                        "id_plano_trabalho"
                    ),
                )

                tabelas[
                    "orgaos_analises_pendentes"
                ].append(linha)

    def _normalizar_analise(
        self,
        analise: dict[str, Any],
        id_plano_acao: int | None,
        tabelas: dict[str, list[dict[str, Any]]],
    ) -> None:
        historico = analise.get("historico") or []

        analise_limpa = {
            chave: valor
            for chave, valor in analise.items()
            if chave != "historico"
        }

        analise_limpa.setdefault(
            "id_plano_acao",
            id_plano_acao,
        )

        self._adicionar_unico(
            tabelas["analises"],
            analise_limpa,
            "id_plano_trabalho_analise_pt",
        )

        for evento in historico:
            linha = dict(evento)

            linha.setdefault(
                "id_plano_trabalho_analise_pt",
                analise.get(
                    "id_plano_trabalho_analise_pt"
                ),
            )

            tabelas[
                "historico_analises"
            ].append(linha)

    def _normalizar_metas(
        self,
        metas: list[dict[str, Any]],
        id_plano_acao: int | None,
        id_executor: int | None,
        tabelas: dict[str, list[dict[str, Any]]],
    ) -> None:
        for meta in metas:
            linha = dict(meta)

            linha.setdefault(
                "id_plano_acao",
                id_plano_acao,
            )

            linha.setdefault(
                "id_executor",
                id_executor,
            )

            self._adicionar_unico(
                tabelas["metas"],
                linha,
                "id_meta",
            )

    def _normalizar_empenhos(
        self,
        empenhos: list[dict[str, Any]],
        id_plano_acao: int | None,
        tabelas: dict[str, list[dict[str, Any]]],
    ) -> None:
        for empenho in empenhos:
            documentos_habeis = (
                empenho.get("documentos_habeis") or []
            )

            empenho_limpo = {
                chave: valor
                for chave, valor in empenho.items()
                if chave != "documentos_habeis"
            }

            empenho_limpo.setdefault(
                "id_plano_acao",
                id_plano_acao,
            )

            self._adicionar_unico(
                tabelas["empenhos"],
                empenho_limpo,
                "id_empenho",
            )

            for documento in documentos_habeis:
                op_ob = documento.get("op_ob") or []

                documento_limpo = {
                    chave: valor
                    for chave, valor in documento.items()
                    if chave != "op_ob"
                }

                documento_limpo.setdefault(
                    "id_empenho",
                    empenho.get("id_empenho"),
                )

                self._adicionar_unico(
                    tabelas["documentos_habeis"],
                    documento_limpo,
                    "id_dh",
                )

                for movimento in op_ob:
                    linha = dict(movimento)

                    linha.setdefault(
                        "id_dh",
                        documento.get("id_dh"),
                    )

                    self._adicionar_unico(
                        tabelas["op_ob"],
                        linha,
                        "id_op_ob",
                    )

    def _normalizar_gestao_financeira(
        self,
        gestao: dict[str, Any],
        id_plano_acao: int | None,
        tabelas: dict[str, list[dict[str, Any]]],
    ) -> None:
        lancamentos = gestao.get("lancamentos") or []
        saldos = gestao.get("saldo_conta") or []

        for lancamento in lancamentos:
            subtransacoes = (
                lancamento.get("subtransacoes") or []
            )

            lancamento_limpo = {
                chave: valor
                for chave, valor in lancamento.items()
                if chave != "subtransacoes"
            }

            lancamento_limpo.setdefault(
                "id_plano_acao",
                id_plano_acao,
            )

            self._adicionar_unico(
                tabelas["lancamentos_financeiros"],
                lancamento_limpo,
                "id_lancamento_gestao_financeira",
            )

            for subtransacao in subtransacoes:
                linha = dict(subtransacao)

                linha.setdefault(
                    "id_lancamento_gestao_financeira",
                    lancamento.get(
                        "id_lancamento_gestao_financeira"
                    ),
                )

                tabelas[
                    "subtransacoes_financeiras"
                ].append(linha)

        for saldo in saldos:
            linha = dict(saldo)

            linha.setdefault(
                "id_plano_acao",
                id_plano_acao,
            )

            tabelas[
                "saldos_conta"
            ].append(linha)

    def _normalizar_relatorios_gestao(
        self,
        relatorios: dict[str, Any],
        id_plano_acao: int | None,
        tabelas: dict[str, list[dict[str, Any]]],
    ) -> None:
        for origem in (
            "novos",
            "legados",
        ):
            for relatorio in (
                relatorios.get(origem) or []
            ):
                linha = dict(relatorio)

                linha["origem_relatorio"] = origem

                linha.setdefault(
                    "id_plano_acao",
                    id_plano_acao,
                )

                tabelas[
                    "relatorios_gestao"
                ].append(linha)

    @staticmethod
    def _adicionar_unico(
        tabela: list[dict[str, Any]],
        registro: dict[str, Any],
        chave: str,
    ) -> None:
        valor = registro.get(chave)

        if valor is None:
            tabela.append(registro)
            return

        existe = any(
            item.get(chave) == valor
            for item in tabela
        )

        if not existe:
            tabela.append(registro)

    @staticmethod
    def _adicionar_unico_composto(
        tabela: list[dict[str, Any]],
        registro: dict[str, Any],
        chaves: list[str],
    ) -> None:
        valores = tuple(
            registro.get(chave)
            for chave in chaves
        )

        existe = any(
            tuple(
                item.get(chave)
                for chave in chaves
            )
            == valores
            for item in tabela
        )

        if not existe:
            tabela.append(registro)
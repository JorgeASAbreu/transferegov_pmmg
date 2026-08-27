from __future__ import annotations

from typing import Any


class ValidadorIntegridade:
    def __init__(
        self,
        tabelas: dict[str, list[dict[str, Any]]],
    ) -> None:
        self.tabelas = tabelas

    def validar(
        self,
    ) -> dict[str, Any]:
        resultado = {
            "planos_trabalho_orfaos": (
                self._validar_planos_trabalho()
            ),
            "historico_planos_trabalho_orfaos": (
                self._validar_historico_planos_trabalho()
            ),
            "analises_orfas": (
                self._validar_analises()
            ),
            "historico_analises_orfaos": (
                self._validar_historico_analises()
            ),
            "empenhos_orfaos": (
                self._validar_empenhos()
            ),
            "documentos_habeis_orfaos": (
                self._validar_documentos_habeis()
            ),
            "op_ob_orfaos": (
                self._validar_op_ob()
            ),
            "lancamentos_orfaos": (
                self._validar_lancamentos()
            ),
            "saldos_orfaos": (
                self._validar_saldos()
            ),
            "relatorios_orfaos": (
                self._validar_relatorios()
            ),
        }

        total_erros = sum(
            len(itens)
            for itens in resultado.values()
        )

        resultado["total_erros"] = total_erros
        resultado["status"] = (
            "OK"
            if total_erros == 0
            else "COM_ERROS"
        )

        return resultado

    def _ids(
        self,
        tabela: str,
        campo: str,
    ) -> set[Any]:
        return {
            registro.get(campo)
            for registro in self.tabelas.get(
                tabela,
                [],
            )
            if registro.get(campo) is not None
        }

    def _validar_planos_trabalho(
        self,
    ) -> list[dict]:
        ids_planos_acao = self._ids(
            "planos_acao",
            "id_plano_acao",
        )

        return [
            registro
            for registro in self.tabelas[
                "planos_trabalho"
            ]
            if registro.get(
                "id_plano_acao"
            )
            not in ids_planos_acao
        ]

    def _validar_historico_planos_trabalho(
        self,
    ) -> list[dict]:
        ids_planos_trabalho = self._ids(
            "planos_trabalho",
            "id_plano_trabalho",
        )

        return [
            registro
            for registro in self.tabelas[
                "historico_planos_trabalho"
            ]
            if registro.get(
                "id_plano_trabalho"
            )
            not in ids_planos_trabalho
        ]

    def _validar_analises(
        self,
    ) -> list[dict]:
        ids_planos_trabalho = self._ids(
            "planos_trabalho",
            "id_plano_trabalho",
        )

        return [
            registro
            for registro in self.tabelas[
                "analises"
            ]
            if registro.get(
                "id_plano_trabalho"
            )
            not in ids_planos_trabalho
        ]

    def _validar_historico_analises(
        self,
    ) -> list[dict]:
        ids_analises = self._ids(
            "analises",
            "id_plano_trabalho_analise_pt",
        )

        return [
            registro
            for registro in self.tabelas[
                "historico_analises"
            ]
            if registro.get(
                "id_plano_trabalho_analise_pt"
            )
            not in ids_analises
        ]

    def _validar_empenhos(
        self,
    ) -> list[dict]:
        ids_planos_acao = self._ids(
            "planos_acao",
            "id_plano_acao",
        )

        return [
            registro
            for registro in self.tabelas[
                "empenhos"
            ]
            if registro.get(
                "id_plano_acao"
            )
            not in ids_planos_acao
        ]

    def _validar_documentos_habeis(
        self,
    ) -> list[dict]:
        ids_empenhos = self._ids(
            "empenhos",
            "id_empenho",
        )

        return [
            registro
            for registro in self.tabelas[
                "documentos_habeis"
            ]
            if registro.get(
                "id_empenho"
            )
            not in ids_empenhos
        ]

    def _validar_op_ob(
        self,
    ) -> list[dict]:
        ids_dh = self._ids(
            "documentos_habeis",
            "id_dh",
        )

        return [
            registro
            for registro in self.tabelas[
                "op_ob"
            ]
            if registro.get(
                "id_dh"
            )
            not in ids_dh
        ]

    def _validar_lancamentos(
        self,
    ) -> list[dict]:
        ids_planos_acao = self._ids(
            "planos_acao",
            "id_plano_acao",
        )

        return [
            registro
            for registro in self.tabelas[
                "lancamentos_financeiros"
            ]
            if registro.get(
                "id_plano_acao"
            )
            not in ids_planos_acao
        ]

    def _validar_saldos(
        self,
    ) -> list[dict]:
        ids_planos_acao = self._ids(
            "planos_acao",
            "id_plano_acao",
        )

        return [
            registro
            for registro in self.tabelas[
                "saldos_conta"
            ]
            if registro.get(
                "id_plano_acao"
            )
            not in ids_planos_acao
        ]

    def _validar_relatorios(
        self,
    ) -> list[dict]:
        ids_planos_acao = self._ids(
            "planos_acao",
            "id_plano_acao",
        )

        return [
            registro
            for registro in self.tabelas[
                "relatorios_gestao"
            ]
            if registro.get(
                "id_plano_acao"
            )
            not in ids_planos_acao
        ]
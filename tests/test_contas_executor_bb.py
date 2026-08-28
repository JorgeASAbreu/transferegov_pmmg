from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from transferegov.integracoes.bb.contas import DescobridorContasBB


class TestDescobridorContasBBExecutor(unittest.TestCase):
    """
    Testes de regressão para a regra:

        conta_consulta_bb = conta_executor

    A conta do Plano de Ação deve ser preservada somente como
    rastreabilidade.
    """

    def _criar_descobridor(
        self,
        registros: list[dict],
    ) -> DescobridorContasBB:
        diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)

        origem = Path(diretorio.name) / "origem.json"
        destino = Path(diretorio.name) / "contas.json"

        origem.write_text(
            json.dumps(
                registros,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return DescobridorContasBB(
            caminho_origem=str(origem),
            caminho_destino=str(destino),
        )

    @staticmethod
    def _registro_79703() -> dict:
        return {
            "executor": {
                "id_executor": 999,
                "codigo_banco_executor": "1",
                "nome_banco_executor": "Banco do Brasil",
                "numero_agencia_executor": "1615",
                "numero_dv_agencia_executor": "2",
                "nome_agencia_executor": "SETOR PUBLICO MG",
                "numero_conta_executor": "26885",
                "numero_dv_conta_executor": "2",
                "codigo_situacao_dado_bancario_executor": 4,
                "descricao_situacao_dado_bancario_executor": "Conta Ativa",
                "id_plano_acao": 79703,
            },
            "plano_acao": {
                "id_plano_acao": 79703,
                "codigo_plano_acao": "09032025-079703",
                "ano_plano_acao": 2025,
                "situacao_plano_acao": "CIENTE",
                "numero_agencia_plano_acao": "1615",
                "dv_agencia_plano_acao": "2",
                "numero_conta_plano_acao": "26884",
                "dv_conta_plano_acao": "4",
                "id_agencia_conta": "1615-26884",
                "descricao_situacao_dado_bancario_plano_acao": "Conta Ativa",
                "nome_objeto": "Aquisição De Armamento Para A Polícia Militar",
                "nome_parlamentar_emenda_plano_acao": "Junio Amaral",
            },
        }

    def test_usa_conta_executor_para_consulta_bb(self) -> None:
        descobridor = self._criar_descobridor(
            [self._registro_79703()]
        )

        contas = descobridor.descobrir()

        self.assertEqual(len(contas), 1)

        conta = contas[0]

        self.assertEqual(
            conta["id_agencia_conta_executor"],
            "1615-26885",
        )
        self.assertEqual(conta["agencia"], "1615")
        self.assertEqual(conta["conta"], "26885")
        self.assertEqual(conta["dv_conta"], "2")
        self.assertEqual(
            conta["origem_conta_consulta_bb"],
            "executor",
        )

    def test_preserva_conta_plano_acao_como_rastreabilidade(self) -> None:
        descobridor = self._criar_descobridor(
            [self._registro_79703()]
        )

        conta = descobridor.descobrir()[0]

        contas_origem = conta["contas_plano_acao_origem"]

        self.assertEqual(len(contas_origem), 1)
        self.assertEqual(
            contas_origem[0]["id_agencia_conta"],
            "1615-26884",
        )

        vinculo = conta["planos_acao"][0]

        self.assertEqual(
            vinculo["conta_plano_acao"]["conta"],
            "26884",
        )

    def test_nao_substitui_executor_pela_conta_plano(self) -> None:
        descobridor = self._criar_descobridor(
            [self._registro_79703()]
        )

        conta = descobridor.descobrir()[0]

        self.assertNotEqual(
            conta["conta"],
            conta["planos_acao"][0][
                "conta_plano_acao"
            ]["conta"],
        )

        self.assertEqual(conta["conta"], "26885")

    def test_agrupa_multiplos_planos_na_mesma_conta_executor(self) -> None:
        registro_1 = self._registro_79703()

        registro_2 = self._registro_79703()
        registro_2["plano_acao"] = dict(
            registro_2["plano_acao"]
        )
        registro_2["executor"] = dict(
            registro_2["executor"]
        )

        registro_2["plano_acao"]["id_plano_acao"] = 79704
        registro_2["plano_acao"]["codigo_plano_acao"] = (
            "09032025-079704"
        )
        registro_2["executor"]["id_plano_acao"] = 79704

        descobridor = self._criar_descobridor(
            [registro_1, registro_2]
        )

        contas = descobridor.descobrir()

        self.assertEqual(len(contas), 1)
        self.assertEqual(
            contas[0]["quantidade_planos_acao"],
            2,
        )
        self.assertTrue(
            contas[0]["conta_compartilhada"]
        )
        self.assertFalse(
            contas[0]["conta_exclusiva_te"]
        )

    def test_sem_conta_executor_nao_cria_consulta_bb(self) -> None:
        registro = self._registro_79703()
        registro["executor"] = dict(registro["executor"])
        registro["executor"]["numero_conta_executor"] = None

        descobridor = self._criar_descobridor([registro])

        self.assertEqual(
            descobridor.descobrir(),
            [],
        )


if __name__ == "__main__":
    unittest.main()

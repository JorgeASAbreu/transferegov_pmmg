from __future__ import annotations

import unittest

from transferegov.transformacao.consolidacao_financeira import (
    ConsolidacaoFinanceira,
)


class TestConsolidacaoBBContaExecutor(unittest.TestCase):
    def test_vincula_bb_por_id_plano_acao_e_preserva_erro(self) -> None:
        transferencias = [
            {
                "id_plano_acao": 1,
                "id_agencia_conta": "1615-ORIGEM1",
                "valor_transferido_centavos": 100_000,
            },
            {
                "id_plano_acao": 2,
                "id_agencia_conta": "1615-ORIGEM2",
                "valor_transferido_centavos": 200_000,
            },
            {
                "id_plano_acao": 3,
                "id_agencia_conta": "1615-ORIGEM3",
                "valor_transferido_centavos": 300_000,
            },
        ]

        dados_bb = [
            {
                "id_agencia_conta_executor": "1615-50001",
                "agencia": "1615",
                "conta": "50001",
                "status_consulta": "OK",
                "verificacao_manual_bb": False,
                "codigo_erro_api_bb": None,
                "saldo_investimento_bb_centavos": 123_456,
                "planos_acao": [{"id_plano_acao": 1}],
            },
            {
                "id_agencia_conta_executor": "1615-50002",
                "agencia": "1615",
                "conta": "50002",
                "status_consulta": "SEM_FUNDOS",
                "verificacao_manual_bb": False,
                "codigo_erro_api_bb": None,
                "saldo_investimento_bb_centavos": None,
                "planos_acao": [{"id_plano_acao": 2}],
            },
            {
                "id_agencia_conta_executor": "1615-50003",
                "agencia": "1615",
                "conta": "50003",
                "status_consulta": "ERRO",
                "verificacao_manual_bb": True,
                "status_http_bb": 400,
                "codigo_erro_api_bb": "107",
                "mensagem_erro_api_bb": (
                    "Código do cliente não compatível "
                    "com agência e conta."
                ),
                "saldo_investimento_bb_centavos": None,
                "planos_acao": [{"id_plano_acao": 3}],
            },
        ]

        resultado = ConsolidacaoFinanceira(
            transferencias=transferencias,
            dados_bb=dados_bb,
        ).consolidar()

        por_id = {
            item["id_plano_acao"]: item
            for item in resultado
        }

        te1 = por_id[1]
        self.assertEqual(
            te1["id_agencia_conta_executor"],
            "1615-50001",
        )
        self.assertEqual(te1["status_dados_bb"], "OK")
        self.assertFalse(te1["verificacao_manual_bb"])
        self.assertEqual(
            te1["saldo_investimento_bb_centavos"],
            123_456,
        )

        te2 = por_id[2]
        self.assertEqual(
            te2["status_dados_bb"],
            "SEM_FUNDOS",
        )
        self.assertFalse(te2["verificacao_manual_bb"])
        self.assertIsNone(
            te2["saldo_investimento_bb_centavos"]
        )

        te3 = por_id[3]
        self.assertEqual(te3["status_dados_bb"], "ERRO")
        self.assertTrue(te3["verificacao_manual_bb"])
        self.assertEqual(te3["codigo_erro_api_bb"], "107")
        self.assertIsNone(
            te3["saldo_investimento_bb_centavos"]
        )


if __name__ == "__main__":
    unittest.main()

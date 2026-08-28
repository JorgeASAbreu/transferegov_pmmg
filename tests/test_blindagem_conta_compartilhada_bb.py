from __future__ import annotations

import unittest

from transferegov.transformacao.consolidacao_financeira import (
    ConsolidacaoFinanceira,
)


class TestBlindagemContaCompartilhadaBB(unittest.TestCase):
    def test_conta_exclusiva_ok_atribui_saldo_a_te(self) -> None:
        transferencias = [
            {
                "id_plano_acao": 1,
                "valor_transferido_centavos": 100_000,
            }
        ]

        dados_bb = [
            {
                "id_agencia_conta_executor": "1615-50001",
                "agencia": "1615",
                "conta": "50001",
                "status_consulta": "OK",
                "verificacao_manual_bb": False,
                "quantidade_planos_acao": 1,
                "saldo_investimento_bb_centavos": 123_456,
                "planos_acao": [{"id_plano_acao": 1}],
            }
        ]

        te = ConsolidacaoFinanceira(
            transferencias=transferencias,
            dados_bb=dados_bb,
        ).consolidar()[0]

        self.assertFalse(
            te["conta_executor_compartilhada"]
        )
        self.assertEqual(
            te["quantidade_tes_conta_executor"],
            1,
        )
        self.assertTrue(te["saldo_bb_atribuivel_te"])
        self.assertEqual(
            te["saldo_investimento_bb_conta_centavos"],
            123_456,
        )
        self.assertEqual(
            te["saldo_investimento_bb_centavos"],
            123_456,
        )
        self.assertIsNone(
            te["motivo_saldo_nao_atribuido"]
        )
        self.assertFalse(te["verificacao_manual_bb"])

    def test_conta_compartilhada_ok_nao_duplica_saldo(self) -> None:
        transferencias = [
            {
                "id_plano_acao": 1,
                "valor_transferido_centavos": 100_000,
            },
            {
                "id_plano_acao": 2,
                "valor_transferido_centavos": 200_000,
            },
        ]

        dados_bb = [
            {
                "id_agencia_conta_executor": "1615-50000",
                "agencia": "1615",
                "conta": "50000",
                "status_consulta": "OK",
                "verificacao_manual_bb": False,
                "quantidade_planos_acao": 2,
                "saldo_investimento_bb_centavos": 100_000_000,
                "planos_acao": [
                    {"id_plano_acao": 1},
                    {"id_plano_acao": 2},
                ],
            }
        ]

        resultado = ConsolidacaoFinanceira(
            transferencias=transferencias,
            dados_bb=dados_bb,
        ).consolidar()

        self.assertEqual(len(resultado), 2)

        for te in resultado:
            self.assertTrue(
                te["conta_executor_compartilhada"]
            )
            self.assertEqual(
                te["quantidade_tes_conta_executor"],
                2,
            )
            self.assertFalse(
                te["saldo_bb_atribuivel_te"]
            )

            # O saldo observado da conta é preservado para
            # rastreabilidade, mas não é atribuído à TE.
            self.assertEqual(
                te[
                    "saldo_investimento_bb_conta_centavos"
                ],
                100_000_000,
            )
            self.assertIsNone(
                te["saldo_investimento_bb_centavos"]
            )
            self.assertEqual(
                te["motivo_saldo_nao_atribuido"],
                "CONTA_EXECUTOR_COMPARTILHADA",
            )

            # Compartilhamento não é erro de API.
            self.assertFalse(
                te["verificacao_manual_bb"]
            )
            self.assertEqual(
                te["status_dados_bb"],
                "OK",
            )

        # Blindagem principal: somar o saldo atribuível às TEs
        # não pode multiplicar o saldo da conta.
        soma_te = sum(
            te["saldo_investimento_bb_centavos"] or 0
            for te in resultado
        )
        self.assertEqual(soma_te, 0)

    def test_sem_fundos_continua_sem_verificacao_manual(self) -> None:
        transferencias = [
            {
                "id_plano_acao": 1,
                "valor_transferido_centavos": 100_000,
            }
        ]

        dados_bb = [
            {
                "id_agencia_conta_executor": "1615-50002",
                "agencia": "1615",
                "conta": "50002",
                "status_consulta": "SEM_FUNDOS",
                "verificacao_manual_bb": False,
                "quantidade_planos_acao": 1,
                "saldo_investimento_bb_centavos": None,
                "planos_acao": [{"id_plano_acao": 1}],
            }
        ]

        te = ConsolidacaoFinanceira(
            transferencias=transferencias,
            dados_bb=dados_bb,
        ).consolidar()[0]

        self.assertFalse(te["verificacao_manual_bb"])
        self.assertFalse(te["saldo_bb_atribuivel_te"])
        self.assertIsNone(
            te["saldo_investimento_bb_centavos"]
        )
        self.assertEqual(
            te["motivo_saldo_nao_atribuido"],
            "SEM_FUNDOS",
        )

    def test_erro_api_continua_exigindo_verificacao(self) -> None:
        transferencias = [
            {
                "id_plano_acao": 1,
                "valor_transferido_centavos": 100_000,
            }
        ]

        dados_bb = [
            {
                "id_agencia_conta_executor": "1615-50003",
                "agencia": "1615",
                "conta": "50003",
                "status_consulta": "ERRO",
                "verificacao_manual_bb": True,
                "status_http_bb": 400,
                "codigo_erro_api_bb": "107",
                "mensagem_erro_api_bb": "Erro de teste",
                "quantidade_planos_acao": 5,
                "saldo_investimento_bb_centavos": None,
                "planos_acao": [{"id_plano_acao": 1}],
            }
        ]

        te = ConsolidacaoFinanceira(
            transferencias=transferencias,
            dados_bb=dados_bb,
        ).consolidar()[0]

        self.assertTrue(te["verificacao_manual_bb"])
        self.assertEqual(
            te["codigo_erro_api_bb"],
            "107",
        )
        self.assertFalse(te["saldo_bb_atribuivel_te"])
        self.assertIsNone(
            te["saldo_investimento_bb_centavos"]
        )


if __name__ == "__main__":
    unittest.main()

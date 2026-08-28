from __future__ import annotations

import unittest

from transferegov.transformacao.transferencia_operacional import (
    TransferenciaOperacionalExecutor,
)


def executor_base(
    *,
    id_plano_acao: int = 1,
    valor: str = "594000.00",
    conta: str = "26885",
) -> dict:
    return {
        "id_executor": 10,
        "id_plano_acao": id_plano_acao,
        "cnpj_executor": "16695025000197",
        "numero_agencia_executor": "1615",
        "numero_conta_executor": conta,
        "vl_custeio_executor": "0.00",
        "vl_investimento_executor": valor,
    }


def lancamento(
    *,
    id_lancamento: str,
    valor: str,
    conta_destino: str = "26885",
    cnpj_favorecido: str = "16695025000197.0",
    descricao: str = "Transferência enviada",
    tipo: str = "D",
    id_plano_acao: int = 1,
) -> dict:
    referencia = (
        "55"
        + "1615"
        + conta_destino.zfill(9)
    )

    return {
        "id_lancamento_gestao_financeira": id_lancamento,
        "id_plano_acao": id_plano_acao,
        "descricao_gestao_financeira": descricao,
        "tipo_operacao_gestao_financeira": tipo,
        "doc_favorecido_gestao_financeira": cnpj_favorecido,
        "numero_referencia_unica_gestao_financeira": referencia,
        "valor_gestao_financeira": valor,
    }


class TestTransferenciaOperacionalExecutor(unittest.TestCase):
    def analisar(
        self,
        executor: dict,
        lancamentos: list[dict],
    ) -> dict:
        tabelas = {
            "executores": [executor],
            "lancamentos_financeiros": lancamentos,
        }

        return TransferenciaOperacionalExecutor(
            tabelas
        ).analisar()[0]

    def test_confirma_principal_exato_e_separa_adicional(self) -> None:
        resultado = self.analisar(
            executor_base(),
            [
                lancamento(
                    id_lancamento="principal",
                    valor="594000.00",
                ),
                lancamento(
                    id_lancamento="adicional",
                    valor="1274.50",
                ),
            ],
        )

        self.assertEqual(
            resultado["status_transferencia_operacional"],
            "CONFIRMADA",
        )
        self.assertFalse(
            resultado[
                "verificacao_manual_transferencia_operacional"
            ]
        )
        self.assertEqual(
            resultado[
                "valor_transferido_operacional_centavos"
            ],
            59_400_000,
        )
        self.assertEqual(
            resultado[
                "valor_movimentacoes_adicionais_executor_centavos"
            ],
            127_450,
        )
        self.assertTrue(
            resultado[
                "tem_movimentacao_adicional_executor"
            ]
        )
        self.assertTrue(
            resultado[
                "verificacao_manual_movimentacao_adicional"
            ]
        )

    def test_plano_com_multiplos_executores_considera_so_pmmg(self) -> None:
        resultado = self.analisar(
            executor_base(
                valor="50490.00",
                conta="26804",
            ),
            [
                lancamento(
                    id_lancamento="pmmg",
                    valor="50490.00",
                    conta_destino="26804",
                ),
                lancamento(
                    id_lancamento="pcmg",
                    valor="148500.00",
                    conta_destino="26805",
                    cnpj_favorecido="18715532000170.0",
                ),
            ],
        )

        self.assertEqual(
            resultado[
                "valor_transferido_operacional_centavos"
            ],
            5_049_000,
        )
        self.assertEqual(
            resultado[
                "quantidade_transferencias_candidatas"
            ],
            1,
        )

    def test_nao_confunde_transferencia_para_outra_conta(self) -> None:
        resultado = self.analisar(
            executor_base(),
            [
                lancamento(
                    id_lancamento="outra-conta",
                    valor="594000.00",
                    conta_destino="99999",
                ),
            ],
        )

        self.assertEqual(
            resultado["status_transferencia_operacional"],
            "SEM_EVIDENCIA_TRANSFERENCIA",
        )
        self.assertIsNone(
            resultado[
                "valor_transferido_operacional_centavos"
            ]
        )
        self.assertTrue(
            resultado[
                "verificacao_manual_transferencia_operacional"
            ]
        )

    def test_candidato_com_valor_divergente_nao_e_assumido(self) -> None:
        resultado = self.analisar(
            executor_base(),
            [
                lancamento(
                    id_lancamento="divergente",
                    valor="500000.00",
                ),
            ],
        )

        self.assertEqual(
            resultado["status_transferencia_operacional"],
            "DIVERGENTE_VALOR_EXECUTOR",
        )
        self.assertIsNone(
            resultado[
                "valor_transferido_operacional_centavos"
            ]
        )
        self.assertTrue(
            resultado[
                "verificacao_manual_transferencia_operacional"
            ]
        )

    def test_multiplas_movimentacoes_iguais_ao_principal_sao_ambiguas(
        self,
    ) -> None:
        resultado = self.analisar(
            executor_base(),
            [
                lancamento(
                    id_lancamento="a",
                    valor="594000.00",
                ),
                lancamento(
                    id_lancamento="b",
                    valor="594000.00",
                ),
            ],
        )

        self.assertEqual(
            resultado["status_transferencia_operacional"],
            "AMBIGUA_MULTIPLAS_PRINCIPAIS",
        )
        self.assertIsNone(
            resultado[
                "valor_transferido_operacional_centavos"
            ]
        )
        self.assertTrue(
            resultado[
                "verificacao_manual_transferencia_operacional"
            ]
        )

    def test_sem_valor_previsto_executor_nao_inventa_zero(self) -> None:
        executor = executor_base()
        executor["vl_custeio_executor"] = None
        executor["vl_investimento_executor"] = None

        resultado = self.analisar(
            executor,
            [],
        )

        self.assertEqual(
            resultado["status_transferencia_operacional"],
            "SEM_VALOR_PREVISTO_EXECUTOR",
        )
        self.assertIsNone(
            resultado["valor_previsto_executor_centavos"]
        )
        self.assertIsNone(
            resultado[
                "valor_transferido_operacional_centavos"
            ]
        )

    def test_referencia_bb_e_estrita(self) -> None:
        resultado = self.analisar(
            executor_base(),
            [
                {
                    **lancamento(
                        id_lancamento="referencia-errada",
                        valor="594000.00",
                    ),
                    "numero_referencia_unica_gestao_financeira": (
                        "551615000026886"
                    ),
                }
            ],
        )

        self.assertEqual(
            resultado["status_transferencia_operacional"],
            "SEM_EVIDENCIA_TRANSFERENCIA",
        )


if __name__ == "__main__":
    unittest.main()

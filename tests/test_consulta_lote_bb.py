from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from transferegov.integracoes.bb.api_investimentos import (
    ErroAPIInvestimentosBB,
)
from transferegov.integracoes.bb.consulta_lote import (
    ConsultaLoteInvestimentosBB,
)


class TestConsultaLoteInvestimentosBB(unittest.TestCase):
    def _criar_base(self, diretorio: str) -> Path:
        registros = [
            {
                "executor": {
                    "codigo_banco_executor": "1",
                    "nome_banco_executor": "Banco do Brasil",
                    "numero_agencia_executor": "1615",
                    "numero_dv_agencia_executor": "2",
                    "numero_conta_executor": "26885",
                    "numero_dv_conta_executor": "2",
                    "descricao_situacao_dado_bancario_executor": "Conta Ativa",
                    "id_plano_acao": 79703,
                },
                "plano_acao": {
                    "id_plano_acao": 79703,
                    "codigo_plano_acao": "09032025-079703",
                    "ano_plano_acao": 2025,
                    "numero_agencia_plano_acao": "1615",
                    "numero_conta_plano_acao": "26884",
                    "id_agencia_conta": "1615-26884",
                },
            },
            {
                "executor": {
                    "codigo_banco_executor": "1",
                    "nome_banco_executor": "Banco do Brasil",
                    "numero_agencia_executor": "1615",
                    "numero_dv_agencia_executor": "2",
                    "numero_conta_executor": "27000",
                    "numero_dv_conta_executor": "1",
                    "descricao_situacao_dado_bancario_executor": "Conta Ativa",
                    "id_plano_acao": 80000,
                },
                "plano_acao": {
                    "id_plano_acao": 80000,
                    "codigo_plano_acao": "09032025-080000",
                    "ano_plano_acao": 2025,
                    "numero_agencia_plano_acao": "1615",
                    "numero_conta_plano_acao": "26999",
                    "id_agencia_conta": "1615-26999",
                },
            },
        ]

        origem = Path(diretorio) / "origem.json"
        origem.write_text(
            json.dumps(registros, ensure_ascii=False),
            encoding="utf-8",
        )
        return origem

    def test_ok_e_erro_107(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            origem = self._criar_base(diretorio)

            api = Mock()
            api.autenticacao.obter_token.return_value = "TOKEN_TESTE"

            api.consultar_saldo_com_token.side_effect = [
                {
                    "quantidadeFundosInvestimento": 1,
                    "listaFundosInvestimento": [
                        {
                            "codigoFundoInvestimento": 1972,
                            "nomeFundoInvestimento": "BB RF CP Automático",
                            "valorSaldoBruto": 495131.09,
                            "valorSaldoLiquidoResgate": 495131.09,
                        }
                    ],
                },
                ErroAPIInvestimentosBB(
                    mensagem=(
                        "Código do cliente não compatível "
                        "com agência e conta."
                    ),
                    agencia="1615",
                    conta="27000",
                    status_http=400,
                    codigo_api="107",
                    detalhes={"code": "107"},
                ),
            ]

            consulta = ConsultaLoteInvestimentosBB(
                caminho_origem=str(origem),
                caminho_contas=str(
                    Path(diretorio) / "contas.json"
                ),
                caminho_resultado=str(
                    Path(diretorio) / "resultado.json"
                ),
                api=api,
            )

            resultados = consulta.executar()

            self.assertEqual(len(resultados), 2)
            api.autenticacao.obter_token.assert_called_once()

            ok = resultados[0]
            erro = resultados[1]

            self.assertEqual(ok["status_consulta"], "OK")
            self.assertFalse(ok["verificacao_manual_bb"])
            self.assertIsNone(ok["codigo_erro_api_bb"])
            self.assertEqual(
                ok["saldo_investimento_bb_centavos"],
                49_513_109,
            )
            self.assertEqual(
                ok["fundos"][0][
                    "valor_saldo_liquido_resgate_centavos"
                ],
                49_513_109,
            )

            self.assertEqual(erro["status_consulta"], "ERRO")
            self.assertTrue(erro["verificacao_manual_bb"])
            self.assertEqual(erro["codigo_erro_api_bb"], "107")
            self.assertEqual(erro["status_http_bb"], 400)
            self.assertIsNone(
                erro["saldo_investimento_bb_centavos"]
            )

    def test_sem_fundos_nao_exige_verificacao_manual(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            origem = self._criar_base(diretorio)

            api = Mock()
            api.autenticacao.obter_token.return_value = "TOKEN_TESTE"

            api.consultar_saldo_com_token.return_value = {
                "quantidadeFundosInvestimento": 0,
                "listaFundosInvestimento": [],
            }

            consulta = ConsultaLoteInvestimentosBB(
                caminho_origem=str(origem),
                caminho_contas=str(
                    Path(diretorio) / "contas.json"
                ),
                caminho_resultado=str(
                    Path(diretorio) / "resultado.json"
                ),
                api=api,
            )

            resultados = consulta.executar(limite=1)

            self.assertEqual(
                resultados[0]["status_consulta"],
                "SEM_FUNDOS",
            )
            self.assertFalse(
                resultados[0]["verificacao_manual_bb"]
            )
            self.assertIsNone(
                resultados[0]["saldo_investimento_bb_centavos"]
            )

    def test_resumo(self) -> None:
        resultados = [
            {
                "status_consulta": "OK",
                "verificacao_manual_bb": False,
            },
            {
                "status_consulta": "SEM_FUNDOS",
                "verificacao_manual_bb": False,
            },
            {
                "status_consulta": "ERRO",
                "verificacao_manual_bb": True,
            },
        ]

        resumo = ConsultaLoteInvestimentosBB.resumir(
            resultados
        )

        self.assertEqual(
            resumo,
            {
                "total": 3,
                "ok": 1,
                "sem_fundos": 1,
                "erro": 1,
                "verificacao_manual": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from pathlib import Path


class TestSchemaV51(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sql = Path(
            "sql/schema_v5_1.sql"
        ).read_text(encoding="utf-8").lower()

    def test_schema_existe(self) -> None:
        self.assertIn(
            "create schema if not exists transferegov",
            self.sql,
        )

    def test_tabelas_minimas(self) -> None:
        esperadas = [
            "etl_carga",
            "dim_executor",
            "dim_plano_acao",
            "dim_conta_executor",
            "rel_plano_conta_executor",
            "f_transferencia",
            "f_transferencia_operacional",
            "f_bb_saldo_conta",
            "f_bb_saldo_te",
            "f_movimento_gestao_financeira",
        ]
        for tabela in esperadas:
            self.assertIn(
                f"transferegov.{tabela}",
                self.sql,
            )

    def test_campos_monetarios_centavos_bigint(self) -> None:
        campos = [
            "valor_transferido_federal_centavos bigint",
            "valor_transferido_operacional_centavos bigint",
            "valor_movimentacoes_adicionais_executor_centavos bigint",
            "valor_liquidado_centavos bigint",
            "valor_pago_centavos bigint",
            "saldo_investimento_bb_conta_centavos bigint",
        ]
        for campo in campos:
            self.assertIn(campo, self.sql)

    def test_percentual_nao_e_float(self) -> None:
        self.assertIn(
            "percentual_execucao numeric(20,10)",
            self.sql,
        )

    def test_adicional_nao_e_nomeado_rendimento(self) -> None:
        self.assertIn(
            "valor_movimentacoes_adicionais_executor_centavos",
            self.sql,
        )


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest


class TestCorrecaoV512(unittest.TestCase):
    def test_schema_nao_cria_unicidade_por_cnpj_conta(self):
        sql = Path("sql/schema_v5_1.sql").read_text(encoding="utf-8")
        self.assertNotIn("CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_executor_cnpj_conta", sql)
        self.assertIn("CREATE INDEX IF NOT EXISTS ix_dim_executor_cnpj_conta", sql)

    def test_migracao_remove_indice_unico_antigo(self):
        sql = Path("sql/migrations/v5_1_2_corrige_dim_executor.sql").read_text(encoding="utf-8")
        self.assertIn("DROP INDEX IF EXISTS transferegov.ux_dim_executor_cnpj_conta", sql)
        self.assertIn("CREATE INDEX IF NOT EXISTS ix_dim_executor_cnpj_conta", sql)

    def test_auditoria_nao_usa_parametro_is_null_ambiguo(self):
        codigo = Path("src/transferegov/persistencia/loader_v5_1.py").read_text(encoding="utf-8")
        self.assertNotIn("CASE WHEN %s IS NULL", codigo)
        self.assertIn("%s::text", codigo)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations
import unittest
from datetime import date, datetime
from transferegov.persistencia.loader_v5_1 import LoaderV51


class TestLoaderV51(unittest.TestCase):
    def test_date_iso(self):
        self.assertEqual(LoaderV51._date("2026-08-28"), date(2026, 8, 28))

    def test_datetime_iso(self):
        self.assertEqual(LoaderV51._datetime("2026-08-28T10:30:00").hour, 10)

    def test_mapa_bruto_vincula_executor_ao_plano(self):
        bruto=[{"plano_acao":{"id_plano_acao":10,"id_agencia_conta":"1615-1"},"executor":{"id_executor":20}}]
        m=LoaderV51._mapas_bruto(bruto)
        self.assertEqual(m["executores_por_plano"][10]["id_executor"],20)

    def test_none_data_permanece_none(self):
        self.assertIsNone(LoaderV51._date(None))
        self.assertIsNone(LoaderV51._datetime(None))

    def test_sha256_deterministico(self):
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.txt"; p.write_text("abc",encoding="utf-8")
            self.assertEqual(LoaderV51._sha256(p), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


if __name__ == "__main__":
    unittest.main()

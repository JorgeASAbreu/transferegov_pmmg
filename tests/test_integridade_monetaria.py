from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path
from typing import Any

from transferegov.transformacao.consolidacao_financeira import (
    ConsolidacaoFinanceira,
)
from transferegov.transformacao.f_transferencia import FTransferencia
from transferegov.transformacao.transformador import (
    TransformadorTransferegov,
)


CAMINHO_DADOS = Path("dados/transferegov_pmmg.json")

CAMPOS_MONETARIOS_ESPERADOS_F_TRANSFERENCIA = {
    "valor_destinado_centavos",
    "valor_custeio_centavos",
    "valor_investimento_centavos",
    "valor_transferido_centavos",
    "valor_rendimentos_centavos",
    "recursos_disponiveis_centavos",
    "valor_empenhado_centavos",
    "valor_liquidado_centavos",
    "valor_pago_centavos",
    "valor_executado_centavos",
    "liquidado_a_pagar_centavos",
    "saldo_financeiro_teorico_centavos",
    "valor_a_executar_centavos",
    "saldo_conta_centavos",
}


class TestIntegridadeMonetaria(unittest.TestCase):
    """
    Testes de blindagem da arquitetura monetária da V5.

    Objetivos:
        1. Garantir que toda coluna terminada em "_centavos" contenha
           apenas int ou None.
        2. Garantir que nenhum float seja aceito nos campos monetários.
        3. Validar a quantidade esperada de Transferências Especiais
           carregadas pelo conjunto de dados de referência.
        4. Validar identidades financeiras quando houver informação
           suficiente.
        5. Garantir que percentual_execucao seja Decimal ou None.

    IMPORTANTE:
        Estes testes não validam a correção jurídica/contábil das fontes.
        Eles validam a integridade técnica e matemática da camada
        analítica.
    """

    @classmethod
    def setUpClass(cls) -> None:
        if not CAMINHO_DADOS.exists():
            raise FileNotFoundError(
                f"Arquivo de dados não encontrado: {CAMINHO_DADOS}"
            )

        tabelas = TransformadorTransferegov(
            str(CAMINHO_DADOS)
        ).normalizar()

        cls.transferencias = FTransferencia(
            tabelas
        ).construir()

    # ==================================================
    # AUXILIARES
    # ==================================================

    def _assert_campos_centavos_validos(
        self,
        registros: list[dict[str, Any]],
    ) -> None:
        """
        Percorre todos os registros e garante que qualquer campo
        terminado em "_centavos" seja int ou None.

        bool é rejeitado explicitamente, embora em Python bool seja
        subclasse de int.
        """
        erros: list[str] = []

        for indice, registro in enumerate(registros):
            identificador = registro.get(
                "id_plano_acao",
                f"indice={indice}",
            )

            for campo, valor in registro.items():
                if not campo.endswith("_centavos"):
                    continue

                if valor is None:
                    continue

                if isinstance(valor, bool):
                    erros.append(
                        f"id_plano_acao={identificador} | "
                        f"{campo} contém bool: {valor!r}"
                    )
                    continue

                if not isinstance(valor, int):
                    erros.append(
                        f"id_plano_acao={identificador} | "
                        f"{campo} deveria ser int ou None, "
                        f"mas é {type(valor).__name__}: {valor!r}"
                    )

        self.assertFalse(
            erros,
            "\nForam encontrados campos monetários inválidos:\n"
            + "\n".join(erros),
        )

    # ==================================================
    # F_TRANSFERENCIA
    # ==================================================

    def test_quantidade_transferencias_referencia(self) -> None:
        """
        O conjunto atual de referência da PMMG possui 90 TEs.

        Se este teste falhar após nova extração válida, a quantidade
        pode ter mudado legitimamente. Nesse caso, atualize o valor
        esperado somente após validar a nova origem dos dados.
        """
        self.assertEqual(
            len(self.transferencias),
            90,
            (
                "Quantidade de TEs diferente do conjunto de referência. "
                "Verifique se o JSON foi atualizado ou se houve perda "
                "de registros durante a transformação."
            ),
        )

    def test_campos_monetarios_esperados_estao_presentes(self) -> None:
        """
        Garante que a convenção de nomes da camada analítica não seja
        removida silenciosamente em manutenção futura.
        """
        self.assertTrue(
            self.transferencias,
            "Nenhuma transferência foi construída.",
        )

        campos_presentes = set(
            self.transferencias[0].keys()
        )

        faltantes = (
            CAMPOS_MONETARIOS_ESPERADOS_F_TRANSFERENCIA
            - campos_presentes
        )

        self.assertFalse(
            faltantes,
            (
                "Campos monetários esperados não encontrados: "
                + ", ".join(sorted(faltantes))
            ),
        )

    def test_todos_campos_centavos_sao_int_ou_none(self) -> None:
        """
        Blindagem principal contra reintrodução de float.

        Percorre todas as 90 TEs e todos os campos terminados
        em "_centavos".
        """
        self._assert_campos_centavos_validos(
            self.transferencias
        )

    def test_caso_referencia_92176(self) -> None:
        """
        Caso de referência já validado manualmente.

        R$ 527.350,00 = 52.735.000 centavos
        saldo R$ 0,09 = 9 centavos
        """
        te = next(
            (
                registro
                for registro in self.transferencias
                if registro.get("id_plano_acao") == 92176
            ),
            None,
        )

        self.assertIsNotNone(
            te,
            "TE de referência id_plano_acao=92176 não encontrada.",
        )

        assert te is not None

        self.assertEqual(
            te["valor_destinado_centavos"],
            52_735_000,
        )

        self.assertEqual(
            te["valor_transferido_centavos"],
            52_735_000,
        )

        self.assertEqual(
            te["saldo_conta_centavos"],
            9,
        )

        self.assertIsInstance(
            te["valor_destinado_centavos"],
            int,
        )

        self.assertIsInstance(
            te["valor_transferido_centavos"],
            int,
        )

        self.assertIsInstance(
            te["saldo_conta_centavos"],
            int,
        )

    # ==================================================
    # CONSOLIDAÇÃO FINANCEIRA
    # ==================================================

    def test_consolidacao_sem_fontes_nao_inventa_zero(self) -> None:
        """
        Sem BB e SIAFI, informações desconhecidas devem continuar None.

        Isso impede que ausência de informação seja confundida com
        R$ 0,00.
        """
        resultado = ConsolidacaoFinanceira(
            transferencias=self.transferencias,
        ).consolidar()

        self._assert_campos_centavos_validos(resultado)

        te = next(
            registro
            for registro in resultado
            if registro.get("id_plano_acao") == 92176
        )

        self.assertIsNone(
            te["valor_rendimentos_centavos"]
        )
        self.assertIsNone(
            te["valor_empenhado_centavos"]
        )
        self.assertIsNone(
            te["valor_liquidado_centavos"]
        )
        self.assertIsNone(
            te["valor_pago_centavos"]
        )
        self.assertIsNone(
            te["recursos_disponiveis_centavos"]
        )
        self.assertIsNone(
            te["consistencia_financeira_interna"]
        )

    def test_identidade_financeira_com_dados_suficientes(self) -> None:
        """
        Valida a identidade:

            saldo_financeiro_teorico
            - valor_a_executar
            = liquidado_a_pagar

        usando um conjunto controlado de BB/SIAFI.

        O teste usa a TE 92176 apenas como registro-base; os valores
        externos são mocks determinísticos para testar a matemática.
        """
        te_original = next(
            registro
            for registro in self.transferencias
            if registro.get("id_plano_acao") == 92176
        )

        dados_bb = [
            {
                "id_agencia_conta": te_original.get(
                    "id_agencia_conta"
                ),
                "valor_rendimentos": "1234.56",
                "saldo_investimento_bb": "300000.00",
                "data_consulta_bb": "2026-08-28",
            }
        ]

        dados_siafi = [
            {
                "id_plano_acao": 92176,
                "valor_empenhado": "400000.00",
                "valor_liquidado": "250000.00",
                "valor_pago": "200000.00",
            }
        ]

        resultado = ConsolidacaoFinanceira(
            transferencias=self.transferencias,
            dados_bb=dados_bb,
            dados_siafi=dados_siafi,
        ).consolidar()

        self._assert_campos_centavos_validos(resultado)

        te = next(
            registro
            for registro in resultado
            if registro.get("id_plano_acao") == 92176
        )

        self.assertEqual(
            te["valor_transferido_centavos"],
            52_735_000,
        )
        self.assertEqual(
            te["valor_rendimentos_centavos"],
            123_456,
        )
        self.assertEqual(
            te["recursos_disponiveis_centavos"],
            52_858_456,
        )
        self.assertEqual(
            te["valor_empenhado_centavos"],
            40_000_000,
        )
        self.assertEqual(
            te["valor_liquidado_centavos"],
            25_000_000,
        )
        self.assertEqual(
            te["valor_pago_centavos"],
            20_000_000,
        )
        self.assertEqual(
            te["valor_executado_centavos"],
            25_000_000,
        )
        self.assertEqual(
            te["liquidado_a_pagar_centavos"],
            5_000_000,
        )
        self.assertEqual(
            te["saldo_financeiro_teorico_centavos"],
            32_858_456,
        )
        self.assertEqual(
            te["valor_a_executar_centavos"],
            27_858_456,
        )
        self.assertEqual(
            te["saldo_investimento_bb_centavos"],
            30_000_000,
        )

        self.assertTrue(
            te["consistencia_financeira_interna"]
        )

        self.assertEqual(
            (
                te["saldo_financeiro_teorico_centavos"]
                - te["valor_a_executar_centavos"]
            ),
            te["liquidado_a_pagar_centavos"],
        )

        percentual = te["percentual_execucao"]

        self.assertIsInstance(
            percentual,
            Decimal,
        )

        self.assertEqual(
            percentual,
            Decimal(25_000_000)
            / Decimal(52_858_456),
        )

    def test_identidades_de_todas_tes_quando_disponiveis(self) -> None:
        """
        Teste genérico para futuras integrações reais.

        Percorre todas as TEs consolidadas e, quando os três indicadores
        necessários estiverem preenchidos, exige a identidade matemática.

        Hoje, sem fontes BB/SIAFI reais passadas neste teste, é possível
        que nenhuma TE satisfaça os requisitos. O teste continuará útil
        automaticamente quando essas integrações forem incorporadas.
        """
        resultado = ConsolidacaoFinanceira(
            transferencias=self.transferencias,
        ).consolidar()

        inconsistencias: list[str] = []

        for te in resultado:
            saldo = te.get(
                "saldo_financeiro_teorico_centavos"
            )
            a_executar = te.get(
                "valor_a_executar_centavos"
            )
            a_pagar = te.get(
                "liquidado_a_pagar_centavos"
            )

            if None in (
                saldo,
                a_executar,
                a_pagar,
            ):
                continue

            if saldo - a_executar != a_pagar:
                inconsistencias.append(
                    (
                        f"id_plano_acao={te.get('id_plano_acao')} | "
                        f"{saldo} - {a_executar} != {a_pagar}"
                    )
                )

        self.assertFalse(
            inconsistencias,
            "\nInconsistências financeiras encontradas:\n"
            + "\n".join(inconsistencias),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

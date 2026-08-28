from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


class DescobridorContasBB:
    """
    Descobre as contas do Banco do Brasil que devem ser consultadas
    pela integração da PMMG.

    REGRA DE NEGÓCIO
    =================
    O Transferegov apresenta dois contextos bancários distintos:

    1. conta_plano_acao
       Conta de ingresso/rastreabilidade do recurso federal no Estado.

    2. conta_executor
       Conta para a qual o recurso é remanejado dentro do Estado e que
       pertence ao executor. Para a PMMG, esta é a conta operacional
       consultável pela API do Banco do Brasil.

    Portanto:

        conta_consulta_bb = conta_executor

    A conta do Plano de Ação é preservada exclusivamente como vínculo
    de origem e rastreabilidade. Ela NÃO é usada para consultar saldo
    ou investimentos na API BB.

    Granularidade da saída:
        1 registro = 1 agência/conta de executor única.

    Uma conta de executor pode estar associada a mais de um Plano de
    Ação. Quando isso ocorrer, todos os vínculos são preservados.
    """

    def __init__(
        self,
        caminho_origem: str = "dados/transferegov_pmmg.json",
        caminho_destino: str = "dados/bb/contas.json",
    ) -> None:
        self.caminho_origem = Path(caminho_origem)
        self.caminho_destino = Path(caminho_destino)

    # ==================================================
    # CARGA
    # ==================================================

    def carregar_dados(self) -> list[dict[str, Any]]:
        if not self.caminho_origem.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {self.caminho_origem}"
            )

        with self.caminho_origem.open(
            "r",
            encoding="utf-8",
        ) as arquivo:
            dados = json.load(arquivo)

        if not isinstance(dados, list):
            raise ValueError(
                "O JSON principal deve conter uma lista de registros."
            )

        return dados

    # ==================================================
    # DESCOBERTA
    # ==================================================

    def descobrir(self) -> list[dict[str, Any]]:
        dados = self.carregar_dados()

        contas: dict[str, dict[str, Any]] = {}
        planos_por_conta: dict[str, list[dict[str, Any]]] = defaultdict(list)
        contas_plano_por_executor: dict[
            str,
            dict[str, dict[str, Any]],
        ] = defaultdict(dict)

        for registro in dados:
            executor = registro.get("executor") or {}
            plano = registro.get("plano_acao") or {}

            dados_executor = self._extrair_conta_executor(executor)

            # Sem conta do executor não existe conta consultável no BB.
            if dados_executor is None:
                continue

            id_conta_executor = dados_executor["id_agencia_conta_executor"]

            plano_vinculado = self._extrair_vinculo_plano(
                plano=plano,
                executor=executor,
            )

            planos_por_conta[id_conta_executor].append(plano_vinculado)

            conta_plano = plano_vinculado.get("conta_plano_acao")

            if conta_plano:
                id_conta_plano = conta_plano.get("id_agencia_conta")

                if id_conta_plano:
                    contas_plano_por_executor[id_conta_executor][
                        id_conta_plano
                    ] = conta_plano

            if id_conta_executor not in contas:
                contas[id_conta_executor] = {
                    **dados_executor,
                    "origem_conta_consulta_bb": "executor",
                    "campo_agencia_origem": "numero_agencia_executor",
                    "campo_conta_origem": "numero_conta_executor",
                    "ativa": self._eh_conta_ativa(executor),
                }

        resultado: list[dict[str, Any]] = []

        for id_conta_executor, conta_base in contas.items():
            planos = planos_por_conta[id_conta_executor]

            anos = sorted(
                {
                    plano["ano_plano_acao"]
                    for plano in planos
                    if plano.get("ano_plano_acao") is not None
                }
            )

            contas_plano_acao = sorted(
                contas_plano_por_executor[id_conta_executor].values(),
                key=lambda item: (
                    item.get("agencia") or "",
                    item.get("conta") or "",
                ),
            )

            quantidade_planos = len(planos)
            conta_compartilhada = quantidade_planos > 1

            resultado.append(
                {
                    **conta_base,
                    "quantidade_planos_acao": quantidade_planos,
                    "planos_acao": planos,
                    "anos_planos_acao": anos,
                    "conta_compartilhada": conta_compartilhada,
                    "conta_exclusiva_te": not conta_compartilhada,
                    "quantidade_contas_plano_acao_origem": (
                        len(contas_plano_acao)
                    ),
                    "contas_plano_acao_origem": contas_plano_acao,
                }
            )

        resultado.sort(
            key=lambda item: (
                item["agencia"],
                item["conta"],
            )
        )

        return resultado

    # ==================================================
    # EXTRAÇÃO DA CONTA DO EXECUTOR
    # ==================================================

    @classmethod
    def _extrair_conta_executor(
        cls,
        executor: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Extrai a conta operacional do executor.

        Esta é a conta utilizada pela API BB.
        """

        agencia = cls._normalizar_numero(
            executor.get("numero_agencia_executor")
        )
        conta = cls._normalizar_numero(
            executor.get("numero_conta_executor")
        )

        if agencia is None or conta is None:
            return None

        dv_agencia = cls._normalizar_texto(
            executor.get("numero_dv_agencia_executor")
        )
        dv_conta = cls._normalizar_texto(
            executor.get("numero_dv_conta_executor")
        )

        return {
            "id_agencia_conta_executor": f"{agencia}-{conta}",
            "banco": cls._normalizar_texto(
                executor.get("nome_banco_executor")
            ),
            "codigo_banco": cls._normalizar_texto(
                executor.get("codigo_banco_executor")
            ),
            "agencia": agencia,
            "dv_agencia": dv_agencia,
            "nome_agencia": cls._normalizar_texto(
                executor.get("nome_agencia_executor")
            ),
            "conta": conta,
            "dv_conta": dv_conta,
            "situacao": cls._normalizar_texto(
                executor.get(
                    "descricao_situacao_dado_bancario_executor"
                )
            ),
            "codigo_situacao": executor.get(
                "codigo_situacao_dado_bancario_executor"
            ),
        }

    # ==================================================
    # VÍNCULO COM O PLANO DE AÇÃO
    # ==================================================

    @classmethod
    def _extrair_vinculo_plano(
        cls,
        plano: dict[str, Any],
        executor: dict[str, Any],
    ) -> dict[str, Any]:
        conta_plano = cls._extrair_conta_plano_acao(plano)

        return {
            "id_plano_acao": plano.get("id_plano_acao"),
            "codigo_plano_acao": plano.get("codigo_plano_acao"),
            "ano_plano_acao": plano.get("ano_plano_acao"),
            "situacao_plano_acao": plano.get("situacao_plano_acao"),
            "nome_objeto": plano.get("nome_objeto"),
            "nome_parlamentar": plano.get(
                "nome_parlamentar_emenda_plano_acao"
            ),
            "conta_plano_acao": conta_plano,
            "id_executor": executor.get("id_executor"),
        }

    @classmethod
    def _extrair_conta_plano_acao(
        cls,
        plano: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Preserva a conta de origem do Plano de Ação apenas para
        rastreabilidade.

        Ela não é utilizada como conta de consulta da API BB.
        """

        agencia = cls._normalizar_numero(
            plano.get("numero_agencia_plano_acao")
        )
        conta = cls._normalizar_numero(
            plano.get("numero_conta_plano_acao")
        )

        # Compatibilidade com registros em que exista apenas
        # o identificador composto "AGENCIA-CONTA".
        if agencia is None or conta is None:
            id_agencia_conta = plano.get("id_agencia_conta")

            if id_agencia_conta:
                agencia_id, conta_id = cls._separar_agencia_conta(
                    str(id_agencia_conta)
                )

                agencia = agencia or agencia_id
                conta = conta or conta_id

        if agencia is None or conta is None:
            return None

        return {
            "id_agencia_conta": f"{agencia}-{conta}",
            "agencia": agencia,
            "dv_agencia": cls._normalizar_texto(
                plano.get("dv_agencia_plano_acao")
            ),
            "conta": conta,
            "dv_conta": cls._normalizar_texto(
                plano.get("dv_conta_plano_acao")
            ),
            "situacao": cls._normalizar_texto(
                plano.get(
                    "descricao_situacao_dado_bancario_plano_acao"
                )
            ),
        }

    # ==================================================
    # REGRAS AUXILIARES
    # ==================================================

    @staticmethod
    def _eh_conta_ativa(
        executor: dict[str, Any],
    ) -> bool | None:
        descricao = executor.get(
            "descricao_situacao_dado_bancario_executor"
        )

        if descricao is None:
            return None

        return str(descricao).strip().casefold() == "conta ativa".casefold()

    @staticmethod
    def _normalizar_numero(
        valor: Any,
    ) -> str | None:
        if valor is None:
            return None

        texto = str(valor).strip()

        if not texto:
            return None

        if not texto.isdigit():
            return None

        return texto

    @staticmethod
    def _normalizar_texto(
        valor: Any,
    ) -> str | None:
        if valor is None:
            return None

        texto = str(valor).strip()

        return texto or None

    @staticmethod
    def _separar_agencia_conta(
        id_agencia_conta: str,
    ) -> tuple[str | None, str | None]:
        """
        Espera o padrão:

            AGENCIA-CONTA

        Exemplo:

            1615-26884
        """

        valor = str(id_agencia_conta).strip()

        if "-" not in valor:
            return None, None

        agencia, conta = valor.split("-", 1)

        agencia = agencia.strip()
        conta = conta.strip()

        if (
            not agencia
            or not conta
            or not agencia.isdigit()
            or not conta.isdigit()
        ):
            return None, None

        return agencia, conta

    # ==================================================
    # SALVAMENTO
    # ==================================================

    def salvar(
        self,
        contas: list[dict[str, Any]],
    ) -> None:
        self.caminho_destino.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.caminho_destino.open(
            "w",
            encoding="utf-8",
        ) as arquivo:
            json.dump(
                contas,
                arquivo,
                ensure_ascii=False,
                indent=2,
            )

    def executar(self) -> list[dict[str, Any]]:
        contas = self.descobrir()
        self.salvar(contas)
        return contas

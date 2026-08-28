from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from transferegov.transformacao.moeda import para_centavos

from .api_investimentos import (
    APIInvestimentosBB,
    ErroAPIInvestimentosBB,
)
from .contas import DescobridorContasBB


STATUS_VALIDOS_SEM_VERIFICACAO = {
    "OK",
    "SEM_FUNDOS",
}


class ConsultaLoteInvestimentosBB:
    """
    Consulta em lote as contas operacionais do executor na API BB.

    REGRA DE QUALIDADE
    ------------------
    Somente os status:
        - OK
        - SEM_FUNDOS

    são aceitos sem verificação manual.

    Qualquer outro retorno deve produzir:
        verificacao_manual_bb = True

    Quando a API BB fornecer um código de erro, ele é preservado em:
        codigo_erro_api_bb

    Ausência de informação nunca é convertida em zero.

    CAMADA MONETÁRIA
    ----------------
    O JSON bruto do BB pode conter números em reais. Esta classe cria
    campos analíticos em centavos inteiros antes de persistir o lote.

    O saldo de investimento utilizado é o saldo líquido de resgate
    informado por fundo. Quando houver mais de um fundo, o total é a
    soma dos saldos líquidos de resgate, desde que todos estejam
    presentes.

    Este módulo NÃO calcula rendimento.
    """

    def __init__(
        self,
        caminho_origem: str = "dados/transferegov_pmmg.json",
        caminho_contas: str = "dados/bb/contas.json",
        caminho_resultado: str = "dados/bb/saldos_investimentos.json",
        api: APIInvestimentosBB | None = None,
    ) -> None:
        self.caminho_origem = caminho_origem
        self.caminho_contas = caminho_contas
        self.caminho_resultado = Path(caminho_resultado)
        self.api = api or APIInvestimentosBB()

    def executar(
        self,
        limite: int | None = None,
    ) -> list[dict[str, Any]]:
        contas = DescobridorContasBB(
            caminho_origem=self.caminho_origem,
            caminho_destino=self.caminho_contas,
        ).executar()

        if limite is not None:
            if limite <= 0:
                raise ValueError("limite deve ser maior que zero.")
            contas = contas[:limite]

        token = self.api.autenticacao.obter_token()

        resultados: list[dict[str, Any]] = []
        total = len(contas)

        for indice, conta in enumerate(contas, start=1):
            agencia = conta["agencia"]
            numero_conta = conta["conta"]

            print(
                f"[{indice}/{total}] "
                f"Consultando agência={agencia} "
                f"conta={numero_conta}"
            )

            resultado_base = {
                "consultado_em": datetime.now().isoformat(
                    timespec="seconds"
                ),
                "id_agencia_conta_executor": conta.get(
                    "id_agencia_conta_executor"
                ),
                "agencia": agencia,
                "dv_agencia": conta.get("dv_agencia"),
                "conta": numero_conta,
                "dv_conta": conta.get("dv_conta"),
                "situacao_conta_executor": conta.get("situacao"),
                "quantidade_planos_acao": conta.get(
                    "quantidade_planos_acao"
                ),
                "planos_acao": conta.get("planos_acao", []),
                "contas_plano_acao_origem": conta.get(
                    "contas_plano_acao_origem",
                    [],
                ),
            }

            try:
                resposta = self.api.consultar_saldo_com_token(
                    agencia=agencia,
                    conta=numero_conta,
                    token=token,
                )

            except ErroAPIInvestimentosBB as erro:
                registro_erro = {
                    **resultado_base,
                    "status_consulta": "ERRO",
                    "verificacao_manual_bb": True,
                    "status_http_bb": erro.status_http,
                    "codigo_erro_api_bb": erro.codigo_api,
                    "mensagem_erro_api_bb": erro.mensagem,
                    "detalhes_erro_api_bb": erro.detalhes,
                    "quantidade_fundos": None,
                    "fundos": None,
                    "saldo_investimento_bb_centavos": None,
                    "erro": str(erro),
                }
                resultados.append(registro_erro)

                codigo = (
                    erro.codigo_api
                    if erro.codigo_api is not None
                    else "SEM_CODIGO"
                )

                print(
                    f"    ERRO | codigo_api={codigo} | "
                    f"{erro.mensagem}"
                )
                continue

            except Exception as erro:
                # Erro local/inesperado também exige verificação
                # manual, mas não inventamos código de API.
                resultados.append(
                    {
                        **resultado_base,
                        "status_consulta": "ERRO",
                        "verificacao_manual_bb": True,
                        "status_http_bb": None,
                        "codigo_erro_api_bb": None,
                        "mensagem_erro_api_bb": str(erro),
                        "detalhes_erro_api_bb": None,
                        "quantidade_fundos": None,
                        "fundos": None,
                        "saldo_investimento_bb_centavos": None,
                        "erro": str(erro),
                    }
                )

                print(
                    "    ERRO | codigo_api=SEM_CODIGO | "
                    f"{erro}"
                )
                continue

            fundos = self._normalizar_fundos(
                resposta.get("listaFundosInvestimento")
            )

            quantidade_fundos = resposta.get(
                "quantidadeFundosInvestimento"
            )

            if quantidade_fundos is None:
                quantidade_fundos = len(fundos)

            status = (
                "OK"
                if quantidade_fundos > 0
                else "SEM_FUNDOS"
            )

            saldo_centavos = (
                self._somar_saldo_liquido_centavos(fundos)
                if status == "OK"
                else None
            )

            resultados.append(
                {
                    **resultado_base,
                    "status_consulta": status,
                    "verificacao_manual_bb": (
                        status
                        not in STATUS_VALIDOS_SEM_VERIFICACAO
                    ),
                    "status_http_bb": 200,
                    "codigo_erro_api_bb": None,
                    "mensagem_erro_api_bb": None,
                    "detalhes_erro_api_bb": None,
                    "quantidade_fundos": quantidade_fundos,
                    "fundos": fundos,
                    "saldo_investimento_bb_centavos": (
                        saldo_centavos
                    ),
                    "erro": None,
                }
            )

            print(
                f"    {status} | "
                f"fundos={quantidade_fundos}"
            )

        self._salvar(resultados)
        return resultados

    @staticmethod
    def _normalizar_fundos(
        fundos: Any,
    ) -> list[dict[str, Any]]:
        if not isinstance(fundos, list):
            return []

        resultado: list[dict[str, Any]] = []

        for fundo in fundos:
            if not isinstance(fundo, dict):
                continue

            registro = dict(fundo)

            registro["valor_saldo_bruto_centavos"] = (
                para_centavos(
                    fundo.get("valorSaldoBruto")
                )
            )

            registro[
                "valor_saldo_liquido_resgate_centavos"
            ] = para_centavos(
                fundo.get("valorSaldoLiquidoResgate")
            )

            resultado.append(registro)

        return resultado

    @staticmethod
    def _somar_saldo_liquido_centavos(
        fundos: list[dict[str, Any]],
    ) -> int | None:
        if not fundos:
            return None

        valores = [
            fundo.get(
                "valor_saldo_liquido_resgate_centavos"
            )
            for fundo in fundos
        ]

        # Não produzir total parcial quando algum fundo não possui
        # saldo líquido informado.
        if any(valor is None for valor in valores):
            return None

        return sum(valores)

    def _salvar(
        self,
        resultados: list[dict[str, Any]],
    ) -> None:
        self.caminho_resultado.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.caminho_resultado.open(
            "w",
            encoding="utf-8",
        ) as arquivo:
            json.dump(
                resultados,
                arquivo,
                ensure_ascii=False,
                indent=2,
            )

    @staticmethod
    def resumir(
        resultados: list[dict[str, Any]],
    ) -> dict[str, int]:
        resumo = {
            "total": len(resultados),
            "ok": 0,
            "sem_fundos": 0,
            "erro": 0,
            "verificacao_manual": 0,
        }

        for item in resultados:
            status = item.get("status_consulta")

            if status == "OK":
                resumo["ok"] += 1
            elif status == "SEM_FUNDOS":
                resumo["sem_fundos"] += 1
            else:
                resumo["erro"] += 1

            if item.get("verificacao_manual_bb") is True:
                resumo["verificacao_manual"] += 1

        return resumo

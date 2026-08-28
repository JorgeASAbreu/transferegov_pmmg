from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from transferegov.transformacao.transformador import TransformadorTransferegov
from transferegov.transformacao.f_transferencia import FTransferencia
from transferegov.transformacao.consolidacao_financeira import ConsolidacaoFinanceira
from transferegov.transformacao.moeda import formatar_reais


ARQUIVO_TRANSFEREGOV = Path("dados/transferegov_pmmg.json")
ARQUIVO_BB = Path("dados/bb/saldos_investimentos.json")
TOTAL_TES_REFERENCIA = 90


def carregar_json(caminho: Path) -> Any:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    with caminho.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def texto(valor: Any) -> str:
    return "NULL" if valor is None else str(valor)


def main() -> None:
    print("=" * 110)
    print("CONSOLIDAÇÃO REAL — 90 TRANSFERÊNCIAS ESPECIAIS + BANCO DO BRASIL")
    print("=" * 110)

    # 1. Normaliza a base federal.
    tabelas = TransformadorTransferegov(
        str(ARQUIVO_TRANSFEREGOV)
    ).normalizar()

    # 2. Constrói a fato de Transferências Especiais.
    transferencias = FTransferencia(tabelas).construir()

    if len(transferencias) != TOTAL_TES_REFERENCIA:
        raise AssertionError(
            f"Esperadas {TOTAL_TES_REFERENCIA} TEs, "
            f"mas foram construídas {len(transferencias)}."
        )

    # 3. Carrega o lote real do BB recém-gerado.
    dados_bb = carregar_json(ARQUIVO_BB)

    # 4. Consolida. SIAFI ainda não entra neste teste.
    consolidadas = ConsolidacaoFinanceira(
        transferencias=transferencias,
        dados_bb=dados_bb,
    ).consolidar()

    if len(consolidadas) != TOTAL_TES_REFERENCIA:
        raise AssertionError(
            "A consolidação alterou a quantidade de TEs."
        )

    status = Counter()
    verificacao_manual = 0
    codigos_erro = Counter()
    saldos_ok = 0
    saldos_none = 0

    print()
    print("-" * 110)

    for numero, te in enumerate(consolidadas, start=1):
        status_bb = te.get("status_dados_bb")
        manual = te.get("verificacao_manual_bb") is True
        codigo_erro = te.get("codigo_erro_api_bb")
        saldo = te.get("saldo_investimento_bb_centavos")

        status[status_bb] += 1

        if manual:
            verificacao_manual += 1

        if codigo_erro is not None:
            codigos_erro[str(codigo_erro)] += 1

        if saldo is None:
            saldos_none += 1
        else:
            saldos_ok += 1

        marcador = "VERIFICAR" if manual else "OK"

        print(
            f"[{numero:02d}/{len(consolidadas)}] "
            f"TE={texto(te.get('codigo_plano_acao'))} | "
            f"id={texto(te.get('id_plano_acao'))} | "
            f"executor={texto(te.get('id_agencia_conta_executor'))} | "
            f"BB={texto(status_bb)} | "
            f"erro={texto(codigo_erro)} | "
            f"saldo={texto(formatar_reais(saldo))} | "
            f"{marcador}"
        )

    print()
    print("=" * 110)
    print("RESUMO DA CONSOLIDAÇÃO")
    print("=" * 110)
    print(f"Total de TEs: {len(consolidadas)}")

    for nome_status, quantidade in sorted(status.items()):
        print(f"{texto(nome_status)}: {quantidade}")

    print(f"Verificação manual: {verificacao_manual}")
    print(f"TEs com saldo BB disponível: {saldos_ok}")
    print(f"TEs com saldo BB indisponível: {saldos_none}")

    if codigos_erro:
        print()
        print("Códigos de erro da API BB:")
        for codigo, quantidade in sorted(codigos_erro.items()):
            print(f"  {codigo}: {quantidade} TE(s)")

    # Regras de qualidade que devem sempre permanecer verdadeiras.
    for te in consolidadas:
        status_bb = te.get("status_dados_bb")
        manual = te.get("verificacao_manual_bb")

        esperado_manual = status_bb not in {
            "OK",
            "SEM_FUNDOS",
        }

        if manual != esperado_manual:
            raise AssertionError(
                "Regra de verificação manual violada para "
                f"TE {te.get('codigo_plano_acao')}: "
                f"status={status_bb!r}, "
                f"verificacao_manual_bb={manual!r}"
            )

        if esperado_manual:
            if te.get("saldo_investimento_bb_centavos") is not None:
                raise AssertionError(
                    "TE com erro/indisponibilidade BB recebeu saldo: "
                    f"{te.get('codigo_plano_acao')}"
                )

        saldo = te.get("saldo_investimento_bb_centavos")

        if saldo is not None:
            if isinstance(saldo, bool) or not isinstance(saldo, int):
                raise AssertionError(
                    "Saldo BB analítico não está em centavos inteiros: "
                    f"{te.get('codigo_plano_acao')} -> {saldo!r}"
                )

    print()
    print("VALIDAÇÃO FINAL: OK")
    print(
        "As 90 TEs foram preservadas e a regra de "
        "verificação manual foi validada."
    )


if __name__ == "__main__":
    main()

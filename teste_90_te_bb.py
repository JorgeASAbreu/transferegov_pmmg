from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ARQUIVO_TES = Path("dados/transferegov_pmmg.json")
ARQUIVO_BB = Path("dados/bb/saldos_investimentos.json")


def carregar_json(caminho: Path) -> Any:
    with caminho.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def normalizar_numero(valor: Any) -> str | None:
    if valor is None:
        return None

    texto = str(valor).strip()

    if not texto:
        return None

    return texto


def chave_executor(registro_te: dict[str, Any]) -> str | None:
    executor = registro_te.get("executor") or {}

    agencia = normalizar_numero(
        executor.get("numero_agencia_executor")
    )
    conta = normalizar_numero(
        executor.get("numero_conta_executor")
    )

    if not agencia or not conta:
        return None

    return f"{agencia}-{conta}"


def indice_bb(
    resultados_bb: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    indice: dict[str, dict[str, Any]] = {}

    for item in resultados_bb:
        chave = item.get("id_agencia_conta_executor")

        if not chave:
            agencia = normalizar_numero(item.get("agencia"))
            conta = normalizar_numero(item.get("conta"))

            if agencia and conta:
                chave = f"{agencia}-{conta}"

        if chave:
            indice[str(chave)] = item

    return indice


def main() -> None:
    tes = carregar_json(ARQUIVO_TES)
    resultados_bb = carregar_json(ARQUIVO_BB)

    if not isinstance(tes, list):
        raise RuntimeError(
            "O arquivo transferegov_pmmg.json não contém uma lista."
        )

    if not isinstance(resultados_bb, list):
        raise RuntimeError(
            "O arquivo saldos_investimentos.json não contém uma lista."
        )

    bb_por_conta = indice_bb(resultados_bb)

    status_por_te: Counter[str] = Counter()

    print("=" * 100)
    print("TESTE DAS TRANSFERÊNCIAS ESPECIAIS X CONTA EXECUTOR X API BB")
    print("=" * 100)

    for numero, registro in enumerate(tes, start=1):
        plano = registro.get("plano_acao") or {}

        id_plano_acao = plano.get("id_plano_acao")
        codigo_plano_acao = plano.get("codigo_plano_acao")

        chave = chave_executor(registro)

        if chave is None:
            status = "SEM_CONTA_EXECUTOR"
            fundos = None
        else:
            resposta_bb = bb_por_conta.get(chave)

            if resposta_bb is None:
                status = "SEM_RESULTADO_BB"
                fundos = None
            else:
                status = (
                    resposta_bb.get("status_consulta")
                    or "SEM_STATUS"
                )
                fundos = resposta_bb.get("quantidade_fundos")

        status_por_te[status] += 1

        print(
            f"[{numero:02d}/{len(tes)}] "
            f"TE={codigo_plano_acao} | "
            f"id={id_plano_acao} | "
            f"conta_executor={chave or 'NULL'} | "
            f"BB={status} | "
            f"fundos={fundos}"
        )

    print()
    print("=" * 100)
    print("RESUMO POR TRANSFERÊNCIA ESPECIAL")
    print("=" * 100)
    print(f"Total de TEs: {len(tes)}")

    for status, quantidade in sorted(status_por_te.items()):
        print(f"{status}: {quantidade}")

    total_classificado = sum(status_por_te.values())

    if total_classificado != len(tes):
        raise AssertionError(
            "Quantidade classificada diferente do total de TEs."
        )

    print()
    print("Validação concluída sem perda de registros.")


if __name__ == "__main__":
    main()

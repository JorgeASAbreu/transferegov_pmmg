from __future__ import annotations
import argparse
from transferegov.persistencia.loader_v5_1 import LoaderV51


def main() -> None:
    p = argparse.ArgumentParser(description="Carga analítica V5.1 Transferegov + BB no PostgreSQL")
    p.add_argument("--transferegov", default="dados/transferegov_pmmg.json")
    p.add_argument("--bb", default="dados/bb/saldos_investimentos.json")
    p.add_argument("--sem-bb", action="store_true")
    p.add_argument("--esperado-tes", type=int, default=None)
    a = p.parse_args()
    resultado = LoaderV51(a.transferegov, None if a.sem_bb else a.bb, a.esperado_tes).executar()
    print("\nCARGA V5.1 CONCLUÍDA")
    for chave, valor in resultado.items():
        print(f"{chave}: {valor}")


if __name__ == "__main__":
    main()

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


# ============================================================
# CONVENÇÃO MONETÁRIA DO PROJETO
# ============================================================
#
# REGRA:
#     Todo valor monetário utilizado na camada analítica
#     deve ser representado internamente como CENTAVOS INTEIROS.
#
# Exemplo:
#
#     R$ 527.350,00
#
# é armazenado como:
#
#     52_735_000
#
# e NÃO como:
#
#     527350.00
#
#
# MOTIVO:
#
# O tipo float utiliza representação binária e não consegue
# representar exatamente diversos valores decimais.
#
# Exemplo possível:
#
#     328584.56
#
# pode resultar internamente em:
#
#     328584.56000000006
#
#
# Para impedir erros acumulados em cálculos financeiros,
# toda conversão de valores externos ocorre nesta camada.
#
#
# IMPORTANTE PARA MANUTENÇÃO:
#
# - NÃO utilizar float para cálculos monetários.
# - NÃO multiplicar diretamente float por 100.
# - NÃO utilizar int(valor * 100).
# - NÃO espalhar conversões monetárias pelo código.
#
# Utilize sempre:
#
#     para_centavos(...)
#
# na entrada dos dados.
#
# A transformação para reais deve ocorrer apenas na camada
# de apresentação por meio de:
#
#     centavos_para_decimal(...)
#
# ou:
#
#     formatar_reais(...)
#
# ============================================================


CENTAVOS_POR_REAL = 100

CENTAVO = Decimal("0.01")


def para_decimal(valor: Any) -> Decimal | None:
    """
    Converte um valor externo para Decimal de maneira controlada.

    A conversão utiliza str(valor) deliberadamente.

    Motivo:
        Decimal(0.1)

    pode carregar a aproximação binária do float.

    Já:

        Decimal(str(0.1))

    resulta em:

        Decimal("0.1")

    Parâmetros
    ----------
    valor:
        Valor recebido de API, JSON, banco de dados ou outra
        fonte externa.

        Valores aceitos normalmente:
            - int
            - float
            - str
            - Decimal
            - None

    Retorno
    -------
    Decimal | None

    None é preservado como None.

    Isso é essencial porque neste projeto:

        ausência de informação != zero
    """

    if valor is None:
        return None

    if isinstance(valor, Decimal):
        return valor

    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError) as erro:
        raise ValueError(
            f"Valor monetário inválido: {valor!r}"
        ) from erro


def para_centavos(valor: Any) -> int | None:
    """
    Converte um valor expresso em reais para centavos inteiros.

    Exemplos
    --------
    >>> para_centavos("527350.00")
    52735000

    >>> para_centavos(1234.56)
    123456

    >>> para_centavos("0.09")
    9

    >>> para_centavos(None)
    None


    REGRA DE ARREDONDAMENTO
    -----------------------
    Caso a fonte forneça fração inferior a um centavo,
    utiliza-se ROUND_HALF_UP.

    Exemplo:

        R$ 10,005

    será convertido para:

        1.001 centavos
        = R$ 10,01


    OBSERVAÇÃO IMPORTANTE
    ---------------------
    Para valores financeiros brasileiros expressos com
    precisão de duas casas decimais, normalmente não haverá
    necessidade de arredondamento.

    O arredondamento existe apenas para tornar explícito e
    determinístico o comportamento quando uma fonte externa
    entregar precisão maior que centavos.
    """

    decimal = para_decimal(valor)

    if decimal is None:
        return None

    valor_em_reais = decimal.quantize(
        CENTAVO,
        rounding=ROUND_HALF_UP,
    )

    valor_em_centavos = (
        valor_em_reais
        * CENTAVOS_POR_REAL
    )

    return int(valor_em_centavos)


def centavos_para_decimal(
    valor_centavos: int | None,
) -> Decimal | None:
    """
    Converte centavos inteiros para Decimal em reais.

    Esta função deve ser utilizada principalmente nas
    fronteiras de saída ou apresentação.

    Exemplo:

        52_735_000
            ↓
        Decimal("527350")

    Nenhum float é utilizado.
    """

    if valor_centavos is None:
        return None

    return (
        Decimal(valor_centavos)
        / CENTAVOS_POR_REAL
    )


def formatar_reais(
    valor_centavos: int | None,
) -> str | None:
    """
    Formata um valor em centavos no padrão monetário brasileiro.

    Exemplo:

        52_735_000
            ↓
        "R$ 527.350,00"

    Esta função é destinada à apresentação.

    O valor armazenado internamente continua sendo inteiro.
    """

    valor_decimal = centavos_para_decimal(
        valor_centavos
    )

    if valor_decimal is None:
        return None

    texto = f"{valor_decimal:,.2f}"

    # Python utiliza inicialmente:
    #
    #     527,350.00
    #
    # Para o padrão brasileiro precisamos:
    #
    #     527.350,00
    #
    texto = (
        texto
        .replace(",", "_")
        .replace(".", ",")
        .replace("_", ".")
    )

    return f"R$ {texto}"
from __future__ import annotations


BASE_URL = (
    "https://api-publica.transferegov.gestao.gov.br"
    "/especiais"
)

CNPJ_PMMG = "16695025000197"

# (timeout de conexão, timeout de leitura)
TIMEOUT = (10, 60)

# A API permite até 200 registros por página.
TAMANHO_PAGINA = 200
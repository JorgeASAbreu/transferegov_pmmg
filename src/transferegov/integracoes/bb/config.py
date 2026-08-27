from __future__ import annotations

import os
from pathlib import Path


def _obrigatoria(nome: str) -> str:
    valor = os.getenv(nome)

    if not valor:
        raise RuntimeError(
            f"Variável de ambiente obrigatória não definida: {nome}"
        )

    return valor


BB_CLIENT_ID = _obrigatoria("BB_CLIENT_ID")
BB_CLIENT_SECRET = _obrigatoria("BB_CLIENT_SECRET")
BB_APP_KEY = _obrigatoria("BB_APP_KEY")

BB_CERT_PATH = Path(
    _obrigatoria("BB_CERT_PATH")
)

BB_KEY_PATH = Path(
    _obrigatoria("BB_KEY_PATH")
)

BB_TOKEN_URL = (
    "https://oauth.bb.com.br/oauth/token"
)

BB_FUNDOS_BASE_URL = (
    "https://fundos.mtls.api.bb.com.br/v1"
)

BB_FUNDOS_SCOPE = "fundos.info"

BB_TIMEOUT = 30
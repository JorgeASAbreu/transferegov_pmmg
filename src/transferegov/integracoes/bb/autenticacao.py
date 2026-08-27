from __future__ import annotations

import requests

from .config import (
    BB_CERT_PATH,
    BB_CLIENT_ID,
    BB_CLIENT_SECRET,
    BB_FUNDOS_SCOPE,
    BB_KEY_PATH,
    BB_TIMEOUT,
    BB_TOKEN_URL,
)


class AutenticacaoBB:
    def obter_token(self) -> str:
        headers = {
            "Content-Type": (
                "application/x-www-form-urlencoded"
            ),
        }

        data = {
            "grant_type": "client_credentials",
            "scope": BB_FUNDOS_SCOPE,
        }

        resposta = requests.post(
            BB_TOKEN_URL,
            headers=headers,
            data=data,
            auth=(
                BB_CLIENT_ID,
                BB_CLIENT_SECRET,
            ),
            cert=(
                str(BB_CERT_PATH),
                str(BB_KEY_PATH),
            ),
            timeout=BB_TIMEOUT,
        )

        resposta.raise_for_status()

        dados = resposta.json()

        token = dados.get(
            "access_token"
        )

        if not token:
            raise RuntimeError(
                "A API do BB não retornou access_token."
            )

        return token
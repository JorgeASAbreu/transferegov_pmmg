from __future__ import annotations

import requests

from .config import carregar_configuracao_bb


class AutenticacaoBB:
    """
    Responsável por obter token OAuth do Banco do Brasil.

    A configuração é carregada apenas no momento da autenticação real,
    evitando dependência de credenciais durante simples imports ou testes
    unitários com mocks.
    """

    def obter_token(self) -> str:
        config = carregar_configuracao_bb()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "client_credentials",
            "scope": config.fundos_scope,
        }

        resposta = requests.post(
            config.token_url,
            headers=headers,
            data=data,
            auth=(
                config.client_id,
                config.client_secret,
            ),
            cert=(
                str(config.cert_path),
                str(config.key_path),
            ),
            timeout=config.timeout,
        )

        resposta.raise_for_status()

        dados = resposta.json()
        token = dados.get("access_token")

        if not token:
            raise RuntimeError(
                "A API do BB não retornou access_token."
            )

        return token

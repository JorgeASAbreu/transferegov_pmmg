from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _obrigatoria(nome: str) -> str:
    """
    Lê uma variável de ambiente obrigatória.

    A validação ocorre somente quando a configuração do Banco do Brasil
    é efetivamente carregada. Isso permite importar os módulos BB e
    executar testes unitários com mocks sem exigir credenciais reais.
    """
    valor = os.getenv(nome)

    if not valor:
        raise RuntimeError(
            f"Variável de ambiente obrigatória não definida: {nome}"
        )

    return valor


@dataclass(frozen=True)
class ConfiguracaoBB:
    """
    Configuração necessária para autenticação e acesso à API de Fundos BB.

    Credenciais e caminhos de certificado não são avaliados no import do
    módulo. Eles são carregados sob demanda por carregar_configuracao_bb().
    """

    client_id: str
    client_secret: str
    app_key: str
    cert_path: Path
    key_path: Path

    token_url: str = "https://oauth.bb.com.br/oauth/token"
    fundos_base_url: str = "https://fundos.mtls.api.bb.com.br/v1"
    fundos_scope: str = "fundos.info"
    timeout: int = 30


def carregar_configuracao_bb() -> ConfiguracaoBB:
    """
    Carrega e valida a configuração BB a partir das variáveis de ambiente.

    Variáveis obrigatórias:
    - BB_CLIENT_ID
    - BB_CLIENT_SECRET
    - BB_APP_KEY
    - BB_CERT_PATH
    - BB_KEY_PATH

    A função deve ser chamada apenas quando uma operação real com a API BB
    for necessária. Testes unitários que utilizem mocks não precisam definir
    essas variáveis.
    """
    return ConfiguracaoBB(
        client_id=_obrigatoria("BB_CLIENT_ID"),
        client_secret=_obrigatoria("BB_CLIENT_SECRET"),
        app_key=_obrigatoria("BB_APP_KEY"),
        cert_path=Path(_obrigatoria("BB_CERT_PATH")),
        key_path=Path(_obrigatoria("BB_KEY_PATH")),
    )

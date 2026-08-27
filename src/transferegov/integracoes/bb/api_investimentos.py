from __future__ import annotations

from typing import Any

import requests

from .autenticacao import AutenticacaoBB
from .config import (
    BB_APP_KEY,
    BB_CERT_PATH,
    BB_FUNDOS_BASE_URL,
    BB_KEY_PATH,
    BB_TIMEOUT,
)


class APIInvestimentosBB:
    """
    Cliente da API de Fundos de Investimentos
    do Banco do Brasil.

    Responsabilidades:
    - obter token OAuth2 via AutenticacaoBB;
    - consultar saldo de investimentos por agência/conta;
    - validar a resposta da API;
    - retornar o JSON bruto recebido do BB.

    Não realiza:
    - persistência;
    - cálculo de rendimento;
    - transformação analítica.
    """

    def __init__(self) -> None:
        self.autenticacao = AutenticacaoBB()

    def consultar_saldo(
        self,
        agencia: str | int,
        conta: str | int,
    ) -> dict[str, Any]:
        agencia_formatada = self._normalizar_numero(
            agencia
        )

        conta_formatada = self._normalizar_numero(
            conta
        )

        token = self.autenticacao.obter_token()

        url = (
            f"{BB_FUNDOS_BASE_URL}"
            f"/saldo/agencia/{agencia_formatada}"
            f"/conta/{conta_formatada}"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        params = {
            "gw-dev-app-key": BB_APP_KEY,
        }

        try:
            resposta = requests.get(
                url,
                headers=headers,
                params=params,
                cert=(
                    str(BB_CERT_PATH),
                    str(BB_KEY_PATH),
                ),
                timeout=BB_TIMEOUT,
            )

        except requests.RequestException as erro:
            raise RuntimeError(
                "Falha de comunicação com a API "
                "de investimentos do BB | "
                f"agencia={agencia_formatada} | "
                f"conta={conta_formatada} | "
                f"erro={erro}"
            ) from erro

        if not resposta.ok:
            detalhe = self._obter_detalhe_erro(
                resposta
            )

            raise RuntimeError(
                "Erro na API de investimentos BB | "
                f"status={resposta.status_code} | "
                f"agencia={agencia_formatada} | "
                f"conta={conta_formatada} | "
                f"resposta={detalhe}"
            )

        try:
            dados = resposta.json()

        except ValueError as erro:
            raise RuntimeError(
                "A API de investimentos do BB "
                "retornou conteúdo não JSON | "
                f"agencia={agencia_formatada} | "
                f"conta={conta_formatada}"
            ) from erro

        if not isinstance(dados, dict):
            raise RuntimeError(
                "Resposta inesperada da API "
                "de investimentos do BB | "
                f"tipo={type(dados).__name__}"
            )

        return dados

    @staticmethod
    def _normalizar_numero(
        valor: str | int,
    ) -> str:
        """
        Normaliza agência e conta sem acrescentar
        dígito verificador.

        Exemplo:
            1615  -> "1615"
            "27418" -> "27418"
        """

        valor_normalizado = str(
            valor
        ).strip()

        if not valor_normalizado:
            raise ValueError(
                "Agência ou conta não pode ser vazia."
            )

        if not valor_normalizado.isdigit():
            raise ValueError(
                "Agência e conta devem conter "
                "somente números."
            )

        return valor_normalizado

    @staticmethod
    def _obter_detalhe_erro(
        resposta: requests.Response,
    ) -> Any:
        """
        Tenta obter a mensagem estruturada devolvida
        pelo BB sem expor Authorization, APP_KEY ou
        outros dados sensíveis.
        """

        try:
            return resposta.json()

        except ValueError:
            texto = resposta.text.strip()

            if not texto:
                return "Resposta sem corpo."

            return texto
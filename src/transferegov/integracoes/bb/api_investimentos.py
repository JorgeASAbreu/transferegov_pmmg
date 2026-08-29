from __future__ import annotations

from typing import Any

import requests

from .autenticacao import AutenticacaoBB
from .config import carregar_configuracao_bb


class ErroAPIInvestimentosBB(RuntimeError):
    """
    Erro estruturado devolvido pela API de investimentos do BB.

    O objetivo desta exceção é preservar separadamente:
    - status HTTP;
    - código de erro da API BB;
    - mensagem da API;
    - detalhes adicionais;
    - agência e conta consultadas.

    Isso evita depender de parsing de texto livre na camada de lote.
    """

    def __init__(
        self,
        *,
        mensagem: str,
        agencia: str,
        conta: str,
        status_http: int | None = None,
        codigo_api: str | None = None,
        detalhes: Any = None,
    ) -> None:
        self.mensagem = mensagem
        self.agencia = agencia
        self.conta = conta
        self.status_http = status_http
        self.codigo_api = (
            str(codigo_api)
            if codigo_api is not None
            else None
        )
        self.detalhes = detalhes

        partes = [mensagem]

        if status_http is not None:
            partes.append(f"status={status_http}")

        if self.codigo_api is not None:
            partes.append(f"codigo_api={self.codigo_api}")

        partes.extend(
            [
                f"agencia={agencia}",
                f"conta={conta}",
            ]
        )

        if detalhes is not None:
            partes.append(f"detalhes={detalhes}")

        super().__init__(" | ".join(partes))


class APIInvestimentosBB:
    """
    Cliente da API de Fundos de Investimentos do Banco do Brasil.

    Regra operacional do projeto:
    - consultar a conta do EXECUTOR;
    - não consultar a conta do Plano de Ação como conta operacional;
    - não enviar dígito verificador na URL;
    - reutilizar um token OAuth2 em processamento em lote.

    A configuração sensível do BB é carregada somente quando uma chamada
    HTTP real é executada. Assim, simples imports e testes com mocks não
    exigem credenciais ou certificados no ambiente.

    Este cliente retorna o JSON bruto do BB.
    A transformação para centavos pertence à camada de integração/lote.
    """

    def __init__(self) -> None:
        self.autenticacao = AutenticacaoBB()

    def consultar_saldo(
        self,
        agencia: str | int,
        conta: str | int,
    ) -> dict[str, Any]:
        token = self.autenticacao.obter_token()

        return self.consultar_saldo_com_token(
            agencia=agencia,
            conta=conta,
            token=token,
        )

    def consultar_saldo_com_token(
        self,
        agencia: str | int,
        conta: str | int,
        token: str,
    ) -> dict[str, Any]:
        agencia_formatada = self._normalizar_numero(agencia)
        conta_formatada = self._normalizar_numero(conta)

        token_normalizado = str(token).strip()

        if not token_normalizado:
            raise ValueError("Token OAuth2 não pode ser vazio.")

        config = carregar_configuracao_bb()

        url = (
            f"{config.fundos_base_url}"
            f"/saldo/agencia/{agencia_formatada}"
            f"/conta/{conta_formatada}"
        )

        headers = {
            "Authorization": f"Bearer {token_normalizado}",
            "Accept": "application/json",
        }

        params = {
            "gw-dev-app-key": config.app_key,
        }

        try:
            resposta = requests.get(
                url,
                headers=headers,
                params=params,
                cert=(
                    str(config.cert_path),
                    str(config.key_path),
                ),
                timeout=config.timeout,
            )

        except requests.RequestException as erro:
            raise ErroAPIInvestimentosBB(
                mensagem=(
                    "Falha de comunicação com a API "
                    "de investimentos do BB"
                ),
                agencia=agencia_formatada,
                conta=conta_formatada,
                detalhes=str(erro),
            ) from erro

        if not resposta.ok:
            detalhe = self._obter_detalhe_erro(resposta)

            codigo_api = None
            mensagem_api = "Erro na API de investimentos BB"

            if isinstance(detalhe, dict):
                codigo_api = detalhe.get("code")

                if detalhe.get("message"):
                    mensagem_api = str(detalhe["message"])

            raise ErroAPIInvestimentosBB(
                mensagem=mensagem_api,
                agencia=agencia_formatada,
                conta=conta_formatada,
                status_http=resposta.status_code,
                codigo_api=codigo_api,
                detalhes=detalhe,
            )

        try:
            dados = resposta.json()

        except ValueError as erro:
            raise ErroAPIInvestimentosBB(
                mensagem=(
                    "A API de investimentos do BB "
                    "retornou conteúdo não JSON"
                ),
                agencia=agencia_formatada,
                conta=conta_formatada,
                status_http=resposta.status_code,
            ) from erro

        if not isinstance(dados, dict):
            raise ErroAPIInvestimentosBB(
                mensagem=(
                    "Resposta inesperada da API "
                    "de investimentos do BB"
                ),
                agencia=agencia_formatada,
                conta=conta_formatada,
                status_http=resposta.status_code,
                detalhes={
                    "tipo_resposta": type(dados).__name__,
                },
            )

        return dados

    @staticmethod
    def _normalizar_numero(
        valor: str | int,
    ) -> str:
        valor_normalizado = str(valor).strip()

        if not valor_normalizado:
            raise ValueError(
                "Agência ou conta não pode ser vazia."
            )

        if not valor_normalizado.isdigit():
            raise ValueError(
                "Agência e conta devem conter somente números."
            )

        return valor_normalizado

    @staticmethod
    def _obter_detalhe_erro(
        resposta: requests.Response,
    ) -> Any:
        """
        Obtém o conteúdo de erro sem expor Authorization,
        APP_KEY ou outros dados sensíveis.
        """
        try:
            return resposta.json()

        except ValueError:
            texto = resposta.text.strip()

            if not texto:
                return "Resposta sem corpo."

            return texto

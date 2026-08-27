from __future__ import annotations

from typing import Any

import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import (
    BASE_URL,
    TAMANHO_PAGINA,
    TIMEOUT,
)
from .logger import configurar_logger


class TransferegovAPI:
    def __init__(self) -> None:
        self.logger = configurar_logger(
            "transferegov.api"
        )

        self.session = self._criar_session()

    def _criar_session(
        self,
    ) -> requests.Session:
        """
        Cria uma sessão HTTP reutilizável com
        política automática de retry.
        """

        session = requests.Session()

        retry = Retry(
            total=5,
            connect=5,
            read=5,
            status=5,
            backoff_factor=1,
            status_forcelist=(
                429,
                500,
                502,
                503,
                504,
            ),
            allowed_methods=("GET",),
            raise_on_status=False,
        )

        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=10,
            pool_maxsize=10,
        )

        session.mount(
            "https://",
            adapter,
        )

        session.mount(
            "http://",
            adapter,
        )

        session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": (
                    "transferegov-pmmg/4.0"
                ),
            }
        )

        return session

    @staticmethod
    def _normalizar_endpoint(
        endpoint: str,
    ) -> str:
        """
        Converte o nome interno do endpoint para o formato
        atual da API pública do Transferegov.

        Internamente, o projeto mantém nomes com underscore
        para preservar compatibilidade com a V4/V5.
        A API HTTP atual utiliza hífens nas rotas.

        Exemplo:
            executores_especiais
            -> executores-especiais
        """

        return endpoint.replace("_", "-")

    def _validar_resposta(
        self,
        resposta: Response,
        endpoint: str,
    ) -> None:
        """
        Verifica se a resposta HTTP foi bem-sucedida.
        """

        if resposta.ok:
            return

        try:
            detalhe = resposta.json()

        except ValueError:
            detalhe = resposta.text

        self.logger.error(
            (
                "Erro HTTP | "
                "endpoint=%s | "
                "status=%s | "
                "url=%s"
            ),
            endpoint,
            resposta.status_code,
            resposta.url,
        )

        raise RuntimeError(
            (
                f"Erro HTTP "
                f"{resposta.status_code} "
                f"no endpoint '{endpoint}'. "
                f"URL: {resposta.url}. "
                f"Resposta: {detalhe}"
            )
        )

    def consultar(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Executa uma requisição GET na API.
        """

        endpoint_http = self._normalizar_endpoint(endpoint)

        url = f"{BASE_URL}/{endpoint_http}"

        self.logger.info(
            "GET | endpoint=%s | params=%s",
            endpoint,
            params,
        )

        try:
            resposta = self.session.get(
                url,
                params=params,
                timeout=TIMEOUT,
            )

        except requests.ConnectTimeout as erro:
            self.logger.error(
                "Timeout de conexão | endpoint=%s",
                endpoint,
            )

            raise RuntimeError(
                (
                    "Timeout de conexão no endpoint "
                    f"'{endpoint}'."
                )
            ) from erro

        except requests.ReadTimeout as erro:
            self.logger.error(
                "Timeout de leitura | endpoint=%s",
                endpoint,
            )

            raise RuntimeError(
                (
                    "Timeout de leitura no endpoint "
                    f"'{endpoint}'."
                )
            ) from erro

        except requests.ConnectionError as erro:
            self.logger.error(
                "Erro de conexão | endpoint=%s",
                endpoint,
            )

            raise RuntimeError(
                (
                    "Erro de conexão com o endpoint "
                    f"'{endpoint}'."
                )
            ) from erro

        except requests.RequestException as erro:
            self.logger.exception(
                (
                    "Erro inesperado na requisição | "
                    "endpoint=%s"
                ),
                endpoint,
            )

            raise RuntimeError(
                (
                    "Erro inesperado ao consultar "
                    f"'{endpoint}': {erro}"
                )
            ) from erro

        self._validar_resposta(
            resposta,
            endpoint,
        )

        self.logger.info(
            "GET concluído | endpoint=%s | status=%s",
            endpoint,
            resposta.status_code,
        )

        try:
            dados = resposta.json()

        except ValueError as erro:
            self.logger.error(
                "JSON inválido | endpoint=%s",
                endpoint,
            )

            raise RuntimeError(
                (
                    f"O endpoint '{endpoint}' "
                    "não retornou JSON válido."
                )
            ) from erro

        if not isinstance(dados, dict):
            raise RuntimeError(
                (
                    "Formato inesperado no endpoint "
                    f"'{endpoint}'. "
                    "Esperado: dict. "
                    "Recebido: "
                    f"{type(dados).__name__}"
                )
            )

        return dados

    def consultar_paginado(
        self,
        endpoint: str,
        filtros: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Percorre automaticamente todas as páginas
        de um endpoint paginado.
        """

        pagina = 1

        resultados: list[
            dict[str, Any]
        ] = []

        filtros = filtros or {}

        while True:
            params = {
                **filtros,
                "pagina": pagina,
                "tamanho_da_pagina": (
                    TAMANHO_PAGINA
                ),
            }

            resposta = self.consultar(
                endpoint,
                params=params,
            )

            dados = resposta.get(
                "data",
                [],
            )

            if not isinstance(dados, list):
                raise RuntimeError(
                    (
                        "Campo 'data' inválido no "
                        f"endpoint '{endpoint}'."
                    )
                )

            resultados.extend(dados)

            total_paginas = resposta.get(
                "total_pages",
                1,
            )

            if not isinstance(
                total_paginas,
                int,
            ):
                raise RuntimeError(
                    (
                        "Campo 'total_pages' inválido "
                        f"no endpoint '{endpoint}'."
                    )
                )

            self.logger.info(
                (
                    "Paginação | "
                    "endpoint=%s | "
                    "pagina=%s/%s | "
                    "registros=%s"
                ),
                endpoint,
                pagina,
                total_paginas,
                len(dados),
            )

            if pagina >= total_paginas:
                break

            pagina += 1

        return resultados
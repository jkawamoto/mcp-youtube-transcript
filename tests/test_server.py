#  test_server.py
#
#  Copyright (c) 2025 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
from typing import Any, TypeGuard

import pytest
from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig

from mcp_youtube_transcript import server, AppContext


def is_webshare_proxy_config(obj: Any) -> TypeGuard[WebshareProxyConfig]:
    return isinstance(obj, WebshareProxyConfig)


def is_generic_proxy_config(obj: Any) -> TypeGuard[GenericProxyConfig]:
    return isinstance(obj, GenericProxyConfig)


@pytest.mark.anyio
async def test_new_server() -> None:
    mcp = server()

    app_ctx: AppContext
    async with mcp.settings.lifespan(mcp) as app_ctx:  # type: ignore
        assert app_ctx.http_client == app_ctx.ytt_api._fetcher._http_client
        assert not app_ctx.http_client.proxies
        assert not app_ctx.ytt_api._fetcher._proxy_config


@pytest.mark.anyio
async def test_new_server_with_webshare_proxy() -> None:
    webshare_proxy_username = "test_user"
    webshare_proxy_password = "test_pass"
    proxy_config = WebshareProxyConfig(webshare_proxy_username, webshare_proxy_password)

    mcp = server(
        webshare_proxy_username=webshare_proxy_username,
        webshare_proxy_password=webshare_proxy_password,
    )

    app_ctx: AppContext
    async with mcp.settings.lifespan(mcp) as app_ctx:  # type: ignore
        assert app_ctx.http_client == app_ctx.ytt_api._fetcher._http_client
        assert app_ctx.http_client.proxies == proxy_config.to_requests_dict()
        assert is_webshare_proxy_config(app_ctx.ytt_api._fetcher._proxy_config)
        assert app_ctx.ytt_api._fetcher._proxy_config.proxy_username == webshare_proxy_username
        assert app_ctx.ytt_api._fetcher._proxy_config.proxy_password == webshare_proxy_password
        assert app_ctx.dlp.params.get("proxy") == proxy_config.to_requests_dict()["https"]


@pytest.mark.anyio
async def test_new_server_with_only_webshare_proxy_user() -> None:
    webshare_proxy_username = "test_user"

    mcp = server(
        webshare_proxy_username=webshare_proxy_username,
    )

    app_ctx: AppContext
    async with mcp.settings.lifespan(mcp) as app_ctx:  # type: ignore
        assert app_ctx.http_client == app_ctx.ytt_api._fetcher._http_client
        assert not app_ctx.http_client.proxies
        assert not app_ctx.ytt_api._fetcher._proxy_config
        assert not app_ctx.dlp.params.get("proxy")


@pytest.mark.anyio
async def test_new_server_with_only_webshare_proxy_password() -> None:
    webshare_proxy_password = "test_pass"

    mcp = server(
        webshare_proxy_password=webshare_proxy_password,
    )

    app_ctx: AppContext
    async with mcp.settings.lifespan(mcp) as app_ctx:  # type: ignore
        assert app_ctx.http_client == app_ctx.ytt_api._fetcher._http_client
        assert not app_ctx.http_client.proxies
        assert not app_ctx.ytt_api._fetcher._proxy_config
        assert not app_ctx.dlp.params.get("proxy")


@pytest.mark.anyio
async def test_new_server_with_generic_proxy() -> None:
    http_proxy = "http://localhost:8080"
    https_proxy = "https://localhost:8080"
    proxy_config = GenericProxyConfig(http_proxy, https_proxy)

    mcp = server(
        http_proxy=http_proxy,
        https_proxy=https_proxy,
    )

    app_ctx: AppContext
    async with mcp.settings.lifespan(mcp) as app_ctx:  # type: ignore
        assert app_ctx.http_client == app_ctx.ytt_api._fetcher._http_client
        assert app_ctx.http_client.proxies == proxy_config.to_requests_dict()
        assert is_generic_proxy_config(app_ctx.ytt_api._fetcher._proxy_config)
        assert app_ctx.ytt_api._fetcher._proxy_config.http_url == http_proxy
        assert app_ctx.ytt_api._fetcher._proxy_config.https_url == https_proxy
        assert app_ctx.dlp.params.get("proxy") == proxy_config.to_requests_dict()["https"]


@pytest.mark.anyio
async def test_new_server_with_http_proxy() -> None:
    http_proxy = "http://localhost:8080"
    proxy_config = GenericProxyConfig(http_proxy)

    mcp = server(
        http_proxy=http_proxy,
    )

    app_ctx: AppContext
    async with mcp.settings.lifespan(mcp) as app_ctx:  # type: ignore
        assert app_ctx.http_client == app_ctx.ytt_api._fetcher._http_client
        assert app_ctx.http_client.proxies == proxy_config.to_requests_dict()
        assert is_generic_proxy_config(app_ctx.ytt_api._fetcher._proxy_config)
        assert app_ctx.ytt_api._fetcher._proxy_config.http_url == http_proxy
        assert app_ctx.ytt_api._fetcher._proxy_config.https_url is None
        assert app_ctx.dlp.params.get("proxy") == proxy_config.to_requests_dict()["http"]


@pytest.mark.anyio
async def test_new_server_with_https_proxy() -> None:
    https_proxy = "https://localhost:8080"
    proxy_config = GenericProxyConfig(https_url=https_proxy)

    mcp = server(
        https_proxy=https_proxy,
    )

    app_ctx: AppContext
    async with mcp.settings.lifespan(mcp) as app_ctx:  # type: ignore
        assert app_ctx.http_client == app_ctx.ytt_api._fetcher._http_client
        assert app_ctx.http_client.proxies == proxy_config.to_requests_dict()
        assert is_generic_proxy_config(app_ctx.ytt_api._fetcher._proxy_config)
        assert app_ctx.ytt_api._fetcher._proxy_config.http_url is None
        assert app_ctx.ytt_api._fetcher._proxy_config.https_url == https_proxy
        assert app_ctx.dlp.params.get("proxy") == proxy_config.to_requests_dict()["https"]

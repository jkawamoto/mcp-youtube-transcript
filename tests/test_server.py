#  test_server.py
#
#  Copyright (c) 2025 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
from typing import Any, TypeGuard, Iterator
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockFixture
from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig

from mcp_youtube_transcript.server import new_server


@pytest.fixture
def mock_api(mocker: MockFixture) -> Iterator[MagicMock]:
    yield mocker.patch("mcp_youtube_transcript.server.YouTubeTranscriptApi")


def is_webshare_proxy_config(obj: Any) -> TypeGuard[WebshareProxyConfig]:
    return isinstance(obj, WebshareProxyConfig)


def is_generic_proxy_config(obj: Any) -> TypeGuard[GenericProxyConfig]:
    return isinstance(obj, GenericProxyConfig)


# def test_new_server(mock_api: MagicMock) -> None:
#     new_server()
#
#     mock_api.assert_called_once_with(proxy_config=None)
#
#
# def test_new_server_with_webshare_proxy(mock_api: MagicMock) -> None:
#     webshare_proxy_username = "test_user"
#     webshare_proxy_password = "test_pass"
#
#     new_server(
#         webshare_proxy_username=webshare_proxy_username,
#         webshare_proxy_password=webshare_proxy_password,
#     )
#
#     mock_api.assert_called_once()
#     proxy_config = mock_api.call_args.kwargs["proxy_config"]
#     assert is_webshare_proxy_config(proxy_config)
#     assert proxy_config.proxy_username == webshare_proxy_username
#     assert proxy_config.proxy_password == webshare_proxy_password
#
#
# def test_new_server_with_only_webshare_proxy_user(mock_api: MagicMock) -> None:
#     webshare_proxy_username = "test_user"
#
#     new_server(
#         webshare_proxy_username=webshare_proxy_username,
#     )
#
#     mock_api.assert_called_once_with(proxy_config=None)
#
#
# def test_new_server_with_only_webshare_proxy_password(mock_api: MagicMock) -> None:
#     webshare_proxy_password = "test_pass"
#
#     new_server(
#         webshare_proxy_password=webshare_proxy_password,
#     )
#
#     mock_api.assert_called_once_with(proxy_config=None)
#
#
# def test_new_server_with_generic_proxy(mock_api: MagicMock) -> None:
#     http_proxy = "http://localhost:8080"
#     https_proxy = "https://localhost:8080"
#
#     new_server(
#         http_proxy=http_proxy,
#         https_proxy=https_proxy,
#     )
#
#     mock_api.assert_called_once()
#     proxy_config = mock_api.call_args.kwargs["proxy_config"]
#     assert is_generic_proxy_config(proxy_config)
#     assert proxy_config.http_url == http_proxy
#     assert proxy_config.https_url == https_proxy
#
#
# def test_new_server_with_http_proxy(mock_api: MagicMock) -> None:
#     http_proxy = "http://localhost:8080"
#
#     new_server(
#         http_proxy=http_proxy,
#     )
#
#     mock_api.assert_called_once()
#     proxy_config = mock_api.call_args.kwargs["proxy_config"]
#     assert is_generic_proxy_config(proxy_config)
#     assert proxy_config.http_url == http_proxy
#
#
# def test_new_server_with_https_proxy(mock_api: MagicMock) -> None:
#     https_proxy = "https://localhost:8080"
#
#     new_server(
#         https_proxy=https_proxy,
#     )
#
#     mock_api.assert_called_once()
#     proxy_config = mock_api.call_args.kwargs["proxy_config"]
#     assert is_generic_proxy_config(proxy_config)
#     assert proxy_config.https_url == https_proxy

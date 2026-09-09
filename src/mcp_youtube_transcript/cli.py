#  cli.py
#
#  Copyright (c) 2025-2026 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
import logging

import rich_click as click

from mcp_youtube_transcript import server


@click.command()
@click.option(
    "--response-limit",
    type=int,
    help="Maximum number of characters each response contains. Set a negative value to disable pagination.",
    default=50000,
)
@click.option(
    "--webshare-proxy-username",
    metavar="NAME",
    envvar="WEBSHARE_PROXY_USERNAME",
    help="Webshare proxy service username.",
)
@click.option(
    "--webshare-proxy-password",
    metavar="PASSWORD",
    envvar="WEBSHARE_PROXY_PASSWORD",
    help="Webshare proxy service password.",
)
@click.option("--http-proxy", metavar="URL", envvar="HTTP_PROXY", help="HTTP proxy server URL.")
@click.option("--https-proxy", metavar="URL", envvar="HTTPS_PROXY", help="HTTPS proxy server URL.")
@click.version_option()
def main(
    response_limit: int | None,
    webshare_proxy_username: str | None,
    webshare_proxy_password: str | None,
    http_proxy: str | None,
    https_proxy: str | None,
) -> None:
    """YouTube Transcript MCP server."""

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("starting Youtube Transcript MCP server")
    server(response_limit, webshare_proxy_username, webshare_proxy_password, http_proxy, https_proxy).run()
    logger.info("closed Youtube Transcript MCP server")

#  cli.py
#
#  Copyright (c) 2025 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
import logging
import re
from urllib.parse import urlparse

import click

from mcp_youtube_transcript import server

# Security constants
MAX_RESPONSE_LIMIT = 10_000_000  # 10MB reasonable maximum
MIN_RESPONSE_LIMIT = 1000        # Minimum viable response size
ALLOWED_PROXY_SCHEMES = {'http', 'https', 'socks4', 'socks5'}


def validate_proxy_url(ctx, param, value):
    """Validate proxy URL for security."""
    if value is None:
        return None
    
    try:
        parsed = urlparse(value)
        if not parsed.scheme:
            raise click.BadParameter("Proxy URL must include scheme (http://, https://, etc.)")
        
        if parsed.scheme.lower() not in ALLOWED_PROXY_SCHEMES:
            raise click.BadParameter(f"Proxy scheme must be one of: {', '.join(ALLOWED_PROXY_SCHEMES)}")
        
        if not parsed.hostname:
            raise click.BadParameter("Proxy URL must include hostname")
        
        # Prevent localhost/internal network access for security
        if parsed.hostname.lower() in ('localhost', '127.0.0.1', '::1'):
            raise click.BadParameter("Localhost proxy URLs are not allowed for security")
        
        # Prevent private IP ranges (basic check)
        if re.match(r'^(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)', parsed.hostname):
            raise click.BadParameter("Private network proxy URLs are not allowed for security")
            
        return value
        
    except ValueError as e:
        raise click.BadParameter(f"Invalid proxy URL: {e}")


def validate_response_limit(ctx, param, value):
    """Validate response limit for resource protection."""
    if value is None:
        return None
    
    if value < 0:  # Allow negative for unlimited (as per original design)
        return value
    
    if value > 0 and value < MIN_RESPONSE_LIMIT:
        raise click.BadParameter(f"Response limit must be at least {MIN_RESPONSE_LIMIT} characters or negative for unlimited")
    
    if value > MAX_RESPONSE_LIMIT:
        raise click.BadParameter(f"Response limit cannot exceed {MAX_RESPONSE_LIMIT} characters")
    
    return value


def validate_username(ctx, param, value):
    """Basic validation for proxy username."""
    if value is None:
        return None
    
    # Basic sanitization - remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
    if len(sanitized) > 255:  # Reasonable username length limit
        raise click.BadParameter("Username too long (max 255 characters)")
    
    return sanitized


@click.command()
@click.option(
    "--response-limit",
    type=int,
    callback=validate_response_limit,
    help="Maximum number of characters each response contains. Set a negative value to disable pagination.",
    default=50000,
)
@click.option(
    "--webshare-proxy-username",
    metavar="NAME",
    envvar="WEBSHARE_PROXY_USERNAME",
    callback=validate_username,
    help="Webshare proxy service username.",
)
@click.option(
    "--webshare-proxy-password",
    metavar="PASSWORD",
    envvar="WEBSHARE_PROXY_PASSWORD",
    help="Webshare proxy service password.",
)
@click.option(
    "--http-proxy",
    metavar="URL",
    envvar="HTTP_PROXY",
    callback=validate_proxy_url,
    help="HTTP proxy server URL."
)
@click.option(
    "--https-proxy",
    metavar="URL", 
    envvar="HTTPS_PROXY",
    callback=validate_proxy_url,
    help="HTTPS proxy server URL."
)
@click.version_option()
def main(
    response_limit: int | None,
    webshare_proxy_username: str | None,
    webshare_proxy_password: str | None,
    http_proxy: str | None,
    https_proxy: str | None,
) -> None:
    """YouTube Transcript MCP server."""

    # Configure logging more securely - use a specific logger instead of basicConfig
    logger = logging.getLogger('mcp_youtube_transcript')
    if not logger.handlers:  # Only configure if not already configured
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    # Avoid logging sensitive proxy information
    proxy_info = "with proxy" if (http_proxy or https_proxy or webshare_proxy_username) else "direct connection"
    logger.info(f"Starting YouTube Transcript MCP server ({proxy_info})")
    
    try:
        server(response_limit, webshare_proxy_username, webshare_proxy_password, http_proxy, https_proxy).run()
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        logger.info("YouTube Transcript MCP server stopped")
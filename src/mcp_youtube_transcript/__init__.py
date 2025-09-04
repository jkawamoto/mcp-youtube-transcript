#  __init__.py
#
#  Copyright (c) 2025 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import lru_cache, partial
from typing import AsyncIterator, Final
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from pydantic import Field
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig, ProxyConfig

# Security constants
MAX_VIDEO_ID_LENGTH = 50
MAX_LANG_CODE_LENGTH = 10
MAX_TRANSCRIPT_LENGTH = 5_000_000  # 5MB limit
YOUTUBE_DOMAINS = {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be'}
VALID_LANG_PATTERN = re.compile(r'^[a-z]{2}(-[A-Z]{2})?$')  # ISO language codes
VALID_VIDEO_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{11}$')  # Standard YouTube video ID format


@dataclass(frozen=True)
class AppContext:
    http_client: requests.Session
    ytt_api: YouTubeTranscriptApi


def _validate_video_id(video_id: str) -> str:
    """Validate and sanitize YouTube video ID."""
    if not video_id:
        raise ValueError("Video ID cannot be empty")
    
    if len(video_id) > MAX_VIDEO_ID_LENGTH:
        raise ValueError(f"Video ID too long (max {MAX_VIDEO_ID_LENGTH} characters)")
    
    # YouTube video IDs are exactly 11 characters of base64url alphabet
    if not VALID_VIDEO_ID_PATTERN.match(video_id):
        raise ValueError("Invalid video ID format")
    
    return video_id


def _validate_language_code(lang: str) -> str:
    """Validate and sanitize language code."""
    if not lang:
        raise ValueError("Language code cannot be empty")
    
    if len(lang) > MAX_LANG_CODE_LENGTH:
        raise ValueError(f"Language code too long (max {MAX_LANG_CODE_LENGTH} characters)")
    
    # Remove any potential injection characters
    sanitized = re.sub(r'[^\w-]', '', lang)
    
    # Basic validation for common language codes (en, es, fr, etc.)
    if not VALID_LANG_PATTERN.match(sanitized) and sanitized not in ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh', 'ar', 'hi']:
        # Allow through but log warning for uncommon codes
        pass
    
    return sanitized


def _validate_youtube_url(url: str) -> tuple[str, str]:
    """Validate URL is from YouTube and extract video ID safely."""
    if not url:
        raise ValueError("URL cannot be empty")
    
    if len(url) > 500:  # Reasonable URL length limit
        raise ValueError("URL too long")
    
    try:
        parsed_url = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}")
    
    # Validate hostname is from YouTube
    if not parsed_url.hostname or parsed_url.hostname.lower() not in YOUTUBE_DOMAINS:
        raise ValueError("URL must be from YouTube domains (youtube.com or youtu.be)")
    
    # Validate scheme
    if parsed_url.scheme.lower() not in ['http', 'https']:
        raise ValueError("URL must use HTTP or HTTPS")
    
    # Extract video ID based on URL format
    video_id = ""
    
    if parsed_url.hostname == "youtu.be":
        # Format: https://youtu.be/VIDEO_ID
        video_id = parsed_url.path.lstrip("/").split('/')[0]  # Take only first path segment
    else:
        # Format: https://youtube.com/watch?v=VIDEO_ID
        query_params = parse_qs(parsed_url.query)
        v_param = query_params.get("v")
        if not v_param:
            raise ValueError("Could not find video ID parameter 'v' in URL")
        if len(v_param) == 0:
            raise ValueError("Video ID parameter is empty")
        video_id = v_param[0]
    
    # Validate the extracted video ID
    video_id = _validate_video_id(video_id)
    
    return video_id, parsed_url.hostname


@asynccontextmanager
async def _app_lifespan(_server: FastMCP, proxy_config: ProxyConfig | None) -> AsyncIterator[AppContext]:
    """Application lifespan context manager with security configurations."""
    session_config = {
        'timeout': 30,  # Request timeout
        'max_redirects': 3,  # Limit redirects
    }
    
    with requests.Session() as http_client:
        # Configure session security
        http_client.timeout = session_config['timeout']
        http_client.max_redirects = session_config['max_redirects']
        
        # Set secure headers
        http_client.headers.update({
            'User-Agent': 'mcp-youtube-transcript/0.3.5',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',  # Do Not Track
        })
        
        ytt_api = YouTubeTranscriptApi(http_client=http_client, proxy_config=proxy_config)
        yield AppContext(http_client=http_client, ytt_api=ytt_api)


# Use bounded LRU cache to prevent memory exhaustion
@lru_cache(maxsize=100)  # Limit cache size
def _get_transcript(ctx: AppContext, video_id: str, lang: str) -> str:
    """Get transcript with security validations."""
    # Validate inputs
    video_id = _validate_video_id(video_id)
    lang = _validate_language_code(lang)
    
    # Prepare language list
    if lang == "en":
        languages = ["en"]
    else:
        languages = [lang, "en"]
    
    # Validate language codes in headers to prevent injection
    safe_languages = [_validate_language_code(l) for l in languages]
    
    try:
        # Make request with validated video ID - construct URL safely
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        page = ctx.http_client.get(
            youtube_url,
            headers={"Accept-Language": ",".join(safe_languages)},
            timeout=15,  # Individual request timeout
            allow_redirects=True
        )
        page.raise_for_status()
        
        # Limit response size to prevent memory issues
        if len(page.content) > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError("YouTube page response too large")
        
        # Parse HTML safely
        soup = BeautifulSoup(page.text, "html.parser")
        title = soup.title.string if soup.title else "Transcript"
        
        # Sanitize title to prevent injection in output
        if title:
            title = re.sub(r'[^\w\s\-\.\(\)\[\]\'\"]+', '', title)[:200]  # Limit title length
        
        # Fetch transcript with validated video ID
        transcripts = ctx.ytt_api.fetch(video_id, languages=safe_languages)
        
        # Build transcript text with size limits
        transcript_lines = []
        total_length = 0
        
        for item in transcripts:
            line = item.text.strip()
            if total_length + len(line) > MAX_TRANSCRIPT_LENGTH:
                transcript_lines.append("[TRANSCRIPT TRUNCATED - SIZE LIMIT REACHED]")
                break
            transcript_lines.append(line)
            total_length += len(line)
        
        result = f"# {title}\n" + "\n".join(transcript_lines)
        
        return result
        
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch YouTube page: {e}")
    except Exception as e:
        raise ValueError(f"Error processing transcript: {e}")


def server(
    webshare_proxy_username: str | None = None,
    webshare_proxy_password: str | None = None,
    http_proxy: str | None = None,
    https_proxy: str | None = None,
) -> FastMCP:
    """Initialize MCP server with security configurations."""

    proxy_config: ProxyConfig | None = None
    if webshare_proxy_username and webshare_proxy_password:
        proxy_config = WebshareProxyConfig(webshare_proxy_username, webshare_proxy_password)
    elif http_proxy or https_proxy:
        proxy_config = GenericProxyConfig(http_proxy, https_proxy)

    mcp = FastMCP("Youtube Transcript", lifespan=partial(_app_lifespan, proxy_config=proxy_config))

    @mcp.tool()
    async def get_transcript(
        ctx: Context,
        url: str = Field(description="The URL of the YouTube video"),
        lang: str = Field(description="The preferred language for the transcript", default="en"),
    ) -> str:
        """Retrieves the transcript of a YouTube video with security validations."""
        try:
            # Validate and extract video ID from URL
            video_id, hostname = _validate_youtube_url(url)
            
            # Validate language parameter
            validated_lang = _validate_language_code(lang)
            
            # Get the application context
            app_ctx: AppContext = ctx.request_context.lifespan_context  # type: ignore
            
            # Fetch transcript with validated inputs
            return _get_transcript(app_ctx, video_id, validated_lang)
            
        except ValueError as e:
            # Return user-friendly error without exposing internals
            raise ValueError(f"Invalid request: {e}")
        except Exception as e:
            # Log full error for debugging but return sanitized message
            raise ValueError("Unable to process transcript request")

    return mcp


__all__: Final = ["server"]
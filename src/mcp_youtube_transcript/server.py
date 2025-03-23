#  server.py
#
#  Copyright (c) 2025 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
import json
from functools import lru_cache
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from mcp.server import FastMCP
from pydantic import Field
from requests import Session
from youtube_transcript_api import YouTubeTranscriptApi, IpBlocked, TranscriptsDisabled
from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig, ProxyConfig



from youtube_transcript_api._transcripts import TranscriptListFetcher

# オリジナルのメソッドを保存しておく
original_extract_captions_json = TranscriptListFetcher._extract_captions_json


# 新しい関数を定義
def patched_extract_captions_json(self, html: str, video_id: str) -> dict:
    splitted_html = html.split("var ytInitialPlayerResponse = ")

    if len(splitted_html) <= 1:
        if 'class="g-recaptcha"' in html:
            raise IpBlocked(video_id)

    json_string = splitted_html[1].split("</script>")[0].strip()
    print(json_string)
    video_data = json.loads(
        json_string.split('};var')[0] + '}' if '};var' in json_string else \
            json_string.rstrip(";")
    )

    self._assert_playability(video_data.get("playabilityStatus"), video_id)

    captions_json = video_data.get("captions", {}).get(
        "playerCaptionsTracklistRenderer"
    )
    if captions_json is None or "captionTracks" not in captions_json:
        raise TranscriptsDisabled(video_id)

    return captions_json



# パッチを適用
TranscriptListFetcher._extract_captions_json = patched_extract_captions_json



def new_server(
    webshare_proxy_username: str | None = None,
    webshare_proxy_password: str | None = None,
    http_proxy: str | None = None,
    https_proxy: str | None = None,
) -> FastMCP:
    """Initializes the MCP server."""

    proxy_config: ProxyConfig | None = None
    if webshare_proxy_username and webshare_proxy_password:
        proxy_config = WebshareProxyConfig(webshare_proxy_username, webshare_proxy_password)
    elif http_proxy or https_proxy:
        proxy_config = GenericProxyConfig(http_proxy, https_proxy)

    client = Session()
    client.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"})
    ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config, http_client=client)

    @lru_cache
    def _get_transcript(video_id: str, lang: str) -> str:
        if lang == "en":
            languages = ["en"]
        else:
            languages = [lang, "en"]

        page = requests.get(
            f"https://www.youtube.com/watch?v={video_id}", headers={"Accept-Language": ",".join(languages)}
        )
        page.raise_for_status()
        soup = BeautifulSoup(page.text, "html.parser")
        title = soup.title.string if soup.title else "Transcript"

        transcripts = ytt_api.fetch(video_id, languages=languages)

        return f"# {title}\n" + "\n".join((item.text for item in transcripts))

    mcp = FastMCP("Youtube Transcript")

    @mcp.tool()
    def get_transcript(
        url: str = Field(description="The URL of the YouTube video"),
        lang: str = Field(description="The preferred language for the transcript", default="en"),
    ) -> str:
        """Retrieves the transcript of a YouTube video."""
        parsed_url = urlparse(url)

        if parsed_url.hostname == "youtu.be":
            video_id = parsed_url.path.lstrip("/")
        else:
            q = parse_qs(parsed_url.query).get("v")
            if q is None:
                raise ValueError(f"couldn't find a video ID from the provided URL: {url}.")
            video_id = q[0]

        return _get_transcript(video_id, lang)

    return mcp

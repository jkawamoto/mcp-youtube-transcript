#  serpbase.py
#
#  Copyright (c) 2025-2026 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
"""Transcripts through the SerpBase API, for the requests YouTube refuses."""

from __future__ import annotations

from typing import Any, Final

import requests
from youtube_transcript_api import FetchedTranscriptSnippet

TRANSCRIPTS_URL: Final = "https://api.serpbase.dev/youtube/transcripts"
TIMEOUT: Final = 60.0


class SerpBaseError(RuntimeError):
    """Raised when SerpBase did not return a usable transcript."""


def _to_snippet(row: dict[str, Any]) -> FetchedTranscriptSnippet | None:
    """Converts one row of the answer into a snippet, or None when the row is empty."""
    text = row.get("text")
    if not text:
        return None
    return FetchedTranscriptSnippet(
        text=text,
        start=float(row.get("start_seconds") or 0.0),
        duration=float(row.get("duration_seconds") or 0.0),
    )


def fetch_transcript(
    http_client: requests.Session, api_key: str, video_id: str, lang: str
) -> list[FetchedTranscriptSnippet]:
    """Fetches a transcript from SerpBase.

    Args:
        http_client: The session the server already holds, so a configured proxy applies here too.
        api_key: SerpBase API key, sent in the ``X-API-Key`` header.
        video_id: The YouTube video ID.
        lang: The preferred language of the transcript.

    Returns:
        The transcript snippets, in the order the API returned them.

    Raises:
        SerpBaseError: The request failed, or the answer carried no transcript.
    """
    try:
        res = http_client.post(
            TRANSCRIPTS_URL,
            json={"id": video_id, "hl": lang or "en"},
            headers={"X-API-Key": api_key},
            timeout=TIMEOUT,
        )
        res.raise_for_status()
        body: dict[str, Any] = res.json()
    except requests.RequestException as exc:
        raise SerpBaseError(f"request failed: {exc}") from exc
    except ValueError as exc:
        raise SerpBaseError("the response was not JSON") from exc

    # SerpBase reports its own failures in `status`; an HTTP 200 is not proof of success.
    status = body.get("status")
    if status != 0:
        raise SerpBaseError(f"status {status}, request_id {body.get('request_id')}")

    snippets = [snippet for snippet in (_to_snippet(row) for row in body.get("transcript") or []) if snippet]
    if not snippets:
        raise SerpBaseError("the answer carried no transcript")
    return snippets

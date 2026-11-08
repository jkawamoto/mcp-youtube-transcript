#  test_serpbase.py
#
#  Copyright (c) 2025-2026 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
from typing import Any

import pytest
import requests
from mcp.server.mcpserver.exceptions import ToolError
from youtube_transcript_api import YouTubeTranscriptApiException

import mcp_youtube_transcript
from mcp_youtube_transcript import AppContext
from mcp_youtube_transcript.serpbase import SerpBaseError, fetch_transcript


class FakeResponse:
    """The part of a requests response the fallback reads."""

    def __init__(self, body: Any, status_code: int = 200) -> None:
        self._body = body
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Client Error")

    def json(self) -> Any:
        return self._body


class FakeSession:
    """A session that records the one request it was asked to send."""

    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.requests: list[dict[str, Any]] = []

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.requests.append({"url": url, **kwargs})
        return self.response


def transcript_body() -> dict[str, Any]:
    return {
        "status": 0,
        "request_id": "r-1",
        "credits_charged": 2,
        "transcript": [
            {"text": "first line", "start_seconds": 1.5, "duration_seconds": 2.0, "language": "en"},
            {"text": "", "start_seconds": 3.5, "duration_seconds": 1.0, "language": "en"},
            {"text": "second line", "start_seconds": 4.5, "duration_seconds": 1.25, "language": "en"},
        ],
    }


def test_fetch_transcript_maps_rows() -> None:
    session = FakeSession(FakeResponse(transcript_body()))

    snippets = fetch_transcript(session, "key", "video_id", "en")  # type: ignore[arg-type]

    assert [(s.text, s.start, s.duration) for s in snippets] == [("first line", 1.5, 2.0), ("second line", 4.5, 1.25)]
    sent = session.requests[0]
    assert sent["url"] == "https://api.serpbase.dev/youtube/transcripts"
    assert sent["json"] == {"id": "video_id", "hl": "en"}
    assert sent["headers"] == {"X-API-Key": "key"}


def test_fetch_transcript_sends_the_language() -> None:
    session = FakeSession(FakeResponse(transcript_body()))

    fetch_transcript(session, "key", "video_id", "ja")  # type: ignore[arg-type]

    assert session.requests[0]["json"] == {"id": "video_id", "hl": "ja"}


def test_fetch_transcript_raises_on_error_status() -> None:
    session = FakeSession(FakeResponse({"status": 1001, "request_id": "r-2"}))

    with pytest.raises(SerpBaseError, match="1001"):
        fetch_transcript(session, "key", "video_id", "en")  # type: ignore[arg-type]


def test_fetch_transcript_raises_on_empty_answer() -> None:
    session = FakeSession(FakeResponse({"status": 0, "request_id": "r-3", "transcript": []}))

    with pytest.raises(SerpBaseError, match="no transcript"):
        fetch_transcript(session, "key", "video_id", "en")  # type: ignore[arg-type]


def test_fetch_transcript_raises_on_http_error() -> None:
    session = FakeSession(FakeResponse({}, status_code=502))

    with pytest.raises(SerpBaseError, match="request failed"):
        fetch_transcript(session, "key", "video_id", "en")  # type: ignore[arg-type]


def make_context(session: FakeSession, api_key: str | None) -> AppContext:
    return AppContext(ytt_api=None, dlp=None, http_client=session, serpbase_api_key=api_key)  # type: ignore[arg-type]


def broken_youtube(monkeypatch: pytest.MonkeyPatch) -> None:
    """Makes the direct path fail the way a blocked IP does."""

    def refuse(*_args: Any, **_kwargs: Any) -> Any:
        raise YouTubeTranscriptApiException("Too many requests")

    monkeypatch.setattr(mcp_youtube_transcript, "_get_video_info", refuse)
    monkeypatch.setattr(mcp_youtube_transcript, "_get_transcript_list", refuse)


def test_snippets_fall_back_to_serpbase(monkeypatch: pytest.MonkeyPatch) -> None:
    broken_youtube(monkeypatch)
    session = FakeSession(FakeResponse(transcript_body()))

    title, snippets = mcp_youtube_transcript._get_transcript_snippets(
        make_context(session, "key"), "https://www.youtube.com/watch?v=fallback", "en"
    )

    assert title == ""
    assert [s.text for s in snippets] == ["first line", "second line"]
    assert session.requests[0]["json"] == {"id": "fallback", "hl": "en"}


def test_snippets_keep_the_error_without_a_key(monkeypatch: pytest.MonkeyPatch) -> None:
    broken_youtube(monkeypatch)
    session = FakeSession(FakeResponse(transcript_body()))

    with pytest.raises(ToolError):
        mcp_youtube_transcript._get_transcript_snippets(
            make_context(session, None), "https://www.youtube.com/watch?v=nokey", "en"
        )

    assert session.requests == []


def test_snippets_keep_the_error_when_serpbase_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    broken_youtube(monkeypatch)
    session = FakeSession(FakeResponse({"status": 1020, "request_id": "r-4"}))

    with pytest.raises(ToolError):
        mcp_youtube_transcript._get_transcript_snippets(
            make_context(session, "key"), "https://www.youtube.com/watch?v=empty-credits", "en"
        )

    assert len(session.requests) == 1

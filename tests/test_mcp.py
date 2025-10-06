#  test_mcp.py
#
#  Copyright (c) 2025 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
from datetime import datetime, timedelta, timezone
import os
from typing import AsyncGenerator

import humanize
import pytest
import requests
from bs4 import BeautifulSoup
from mcp import StdioServerParameters, stdio_client, ClientSession
from mcp.types import TextContent
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
from yt_dlp.extractor.youtube import YoutubeIE

from mcp_youtube_transcript import Transcript, VideoInfo, _parse_time_info, TimedTranscript, TranscriptSnippet


def fetch_title(url: str, lang: str) -> str:
    res = requests.get(f"https://www.youtube.com/watch?v={url}", headers={"Accept-Language": lang})
    soup = BeautifulSoup(res.text, "html.parser")
    return soup.title.string or "" if soup.title else ""


@pytest.fixture(scope="module")
async def mcp_client_session() -> AsyncGenerator[ClientSession, None]:
    params = StdioServerParameters(command="uv", args=["run", "mcp-youtube-transcript", "--response-limit", "-1"])
    async with stdio_client(params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            yield session


@pytest.fixture(scope="module")
async def mcp_client_session_with_response_limit() -> AsyncGenerator[ClientSession, None]:
    params = StdioServerParameters(command="uv", args=["run", "mcp-youtube-transcript", "--response-limit", "3000"])
    async with stdio_client(params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            yield session


@pytest.mark.anyio
async def test_list_tools(mcp_client_session: ClientSession) -> None:
    res = await mcp_client_session.list_tools()
    assert any(tool.name == "get_transcript" for tool in res.tools)
    assert any(tool.name == "get_timed_transcript" for tool in res.tools)
    assert any(tool.name == "get_video_info" for tool in res.tools)


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
@pytest.mark.default_cassette("LPZh9BOjkQs.yaml")
@pytest.mark.vcr
@pytest.mark.anyio
async def test_get_transcript(mcp_client_session: ClientSession) -> None:
    video_id = "LPZh9BOjkQs"

    expect = Transcript(
        title=fetch_title(video_id, "en"),
        transcript="\n".join((item.text for item in YouTubeTranscriptApi().fetch(video_id))),
    )

    res = await mcp_client_session.call_tool(
        "get_transcript",
        arguments={"url": f"https://www.youtube.com/watch?v={video_id}"},
    )
    assert isinstance(res.content[0], TextContent)

    transcript = Transcript.model_validate_json(res.content[0].text)
    assert transcript == expect
    assert not res.isError


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
@pytest.mark.default_cassette("WjAXZkQSE2U.yaml")
@pytest.mark.vcr
@pytest.mark.anyio
async def test_get_transcript_with_language(mcp_client_session: ClientSession) -> None:
    video_id = "WjAXZkQSE2U"

    expect = Transcript(
        title=fetch_title(video_id, "ja"),
        transcript="\n".join((item.text for item in YouTubeTranscriptApi().fetch(video_id, ["ja"]))),
    )

    res = await mcp_client_session.call_tool(
        "get_transcript",
        arguments={"url": f"https://www.youtube.com/watch?v={video_id}", "lang": "ja"},
    )
    assert isinstance(res.content[0], TextContent)

    transcript = Transcript.model_validate_json(res.content[0].text)
    assert transcript == expect
    assert not res.isError


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
@pytest.mark.default_cassette("LPZh9BOjkQs.yaml")
@pytest.mark.vcr
@pytest.mark.anyio
async def test_get_transcript_fallback_language(
    mcp_client_session: ClientSession,
) -> None:
    video_id = "LPZh9BOjkQs"

    expect = Transcript(
        title=fetch_title(video_id, "en"),
        transcript="\n".join((item.text for item in YouTubeTranscriptApi().fetch(video_id))),
    )

    res = await mcp_client_session.call_tool(
        "get_transcript",
        arguments={
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "lang": "unknown",
        },
    )
    assert isinstance(res.content[0], TextContent)

    transcript = Transcript.model_validate_json(res.content[0].text)
    assert transcript == expect
    assert not res.isError


@pytest.mark.anyio
async def test_get_transcript_invalid_url(mcp_client_session: ClientSession) -> None:
    res = await mcp_client_session.call_tool(
        "get_transcript", arguments={"url": "https://www.youtube.com/watch?vv=abcdefg"}
    )
    assert res.isError


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
@pytest.mark.default_cassette("error.yaml")
@pytest.mark.vcr
@pytest.mark.anyio
async def test_get_transcript_not_found(mcp_client_session: ClientSession) -> None:
    res = await mcp_client_session.call_tool("get_transcript", arguments={"url": "https://www.youtube.com/watch?v=a"})
    assert res.isError


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
@pytest.mark.default_cassette("LPZh9BOjkQs.yaml")
@pytest.mark.vcr
@pytest.mark.anyio
async def test_get_transcript_with_short_url(mcp_client_session: ClientSession) -> None:
    video_id = "LPZh9BOjkQs"

    expect = Transcript(
        title=fetch_title(video_id, "en"),
        transcript="\n".join((item.text for item in YouTubeTranscriptApi().fetch(video_id))),
    )

    res = await mcp_client_session.call_tool(
        "get_transcript",
        arguments={"url": f"https://youtu.be/{video_id}"},
    )
    assert isinstance(res.content[0], TextContent)

    transcript = Transcript.model_validate_json(res.content[0].text)
    assert transcript == expect
    assert not res.isError


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
@pytest.mark.default_cassette("LPZh9BOjkQs.yaml")
@pytest.mark.vcr
@pytest.mark.anyio
async def test_get_transcript_with_response_limit(mcp_client_session_with_response_limit: ClientSession) -> None:
    video_id = "LPZh9BOjkQs"

    expect = Transcript(
        title=fetch_title(video_id, "en"),
        transcript="\n".join((item.text for item in YouTubeTranscriptApi().fetch(video_id))),
    )

    transcript = ""
    cursor = None
    while True:
        res = await mcp_client_session_with_response_limit.call_tool(
            "get_transcript",
            arguments={"url": f"https://www.youtube.com/watch?v={video_id}", "next_cursor": cursor},
        )
        assert not res.isError
        assert isinstance(res.content[0], TextContent)

        t = Transcript.model_validate_json(res.content[0].text)
        transcript += t.transcript + "\n"
        if t.next_cursor is None:
            break
        cursor = t.next_cursor

    assert t.title == expect.title
    assert transcript[:-1] == expect.transcript


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
@pytest.mark.default_cassette("LPZh9BOjkQs.yaml")
@pytest.mark.vcr
@pytest.mark.anyio
async def test_get_timed_transcript(mcp_client_session: ClientSession) -> None:
    video_id = "LPZh9BOjkQs"

    expect = TimedTranscript(
        title=fetch_title(video_id, "en"),
        snippets=[TranscriptSnippet.from_fetched_transcript_snippet(s) for s in YouTubeTranscriptApi().fetch(video_id)],
    )

    res = await mcp_client_session.call_tool(
        "get_timed_transcript",
        arguments={"url": f"https://www.youtube.com/watch?v={video_id}"},
    )
    assert isinstance(res.content[0], TextContent)

    transcript = TimedTranscript.model_validate_json(res.content[0].text)
    assert transcript == expect
    assert not res.isError


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
@pytest.mark.default_cassette("WjAXZkQSE2U.yaml")
@pytest.mark.vcr
@pytest.mark.anyio
async def test_get_timed_transcript_with_language(mcp_client_session: ClientSession) -> None:
    video_id = "WjAXZkQSE2U"

    expect = TimedTranscript(
        title=fetch_title(video_id, "ja"),
        snippets=[
            TranscriptSnippet.from_fetched_transcript_snippet(s) for s in YouTubeTranscriptApi().fetch(video_id, ["ja"])
        ],
    )

    res = await mcp_client_session.call_tool(
        "get_timed_transcript",
        arguments={"url": f"https://www.youtube.com/watch?v={video_id}", "lang": "ja"},
    )
    assert isinstance(res.content[0], TextContent)
    print(res.content[0].text)

    transcript = TimedTranscript.model_validate_json(res.content[0].text)
    assert transcript == expect
    assert not res.isError


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
@pytest.mark.default_cassette("LPZh9BOjkQs.yaml")
@pytest.mark.vcr
@pytest.mark.anyio
async def test_get_timed_transcript_fallback_language(
    mcp_client_session: ClientSession,
) -> None:
    video_id = "LPZh9BOjkQs"

    expect = TimedTranscript(
        title=fetch_title(video_id, "en"),
        snippets=[TranscriptSnippet.from_fetched_transcript_snippet(s) for s in YouTubeTranscriptApi().fetch(video_id)],
    )

    res = await mcp_client_session.call_tool(
        "get_timed_transcript",
        arguments={
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "lang": "unknown",
        },
    )
    assert isinstance(res.content[0], TextContent)

    transcript = TimedTranscript.model_validate_json(res.content[0].text)
    assert transcript == expect
    assert not res.isError


@pytest.mark.anyio
async def test_get_timed_transcript_invalid_url(mcp_client_session: ClientSession) -> None:
    res = await mcp_client_session.call_tool(
        "get_timed_transcript", arguments={"url": "https://www.youtube.com/watch?vv=abcdefg"}
    )
    assert res.isError


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
@pytest.mark.default_cassette("error.yaml")
@pytest.mark.vcr
@pytest.mark.anyio
async def test_get_timed_transcript_not_found(mcp_client_session: ClientSession) -> None:
    res = await mcp_client_session.call_tool(
        "get_timed_transcript", arguments={"url": "https://www.youtube.com/watch?v=a"}
    )
    assert res.isError


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
@pytest.mark.default_cassette("LPZh9BOjkQs.yaml")
@pytest.mark.vcr
@pytest.mark.anyio
async def test_get_timed_transcript_with_short_url(mcp_client_session: ClientSession) -> None:
    video_id = "LPZh9BOjkQs"

    expect = TimedTranscript(
        title=fetch_title(video_id, "en"),
        snippets=[TranscriptSnippet.from_fetched_transcript_snippet(s) for s in YouTubeTranscriptApi().fetch(video_id)],
    )

    res = await mcp_client_session.call_tool(
        "get_timed_transcript",
        arguments={"url": f"https://youtu.be/{video_id}"},
    )
    assert isinstance(res.content[0], TextContent)

    transcript = TimedTranscript.model_validate_json(res.content[0].text)
    assert transcript == expect
    assert not res.isError


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
@pytest.mark.default_cassette("LPZh9BOjkQs.yaml")
@pytest.mark.vcr
@pytest.mark.anyio
async def test_get_timed_transcript_with_response_limit(mcp_client_session_with_response_limit: ClientSession) -> None:
    video_id = "LPZh9BOjkQs"

    expect = TimedTranscript(
        title=fetch_title(video_id, "en"),
        snippets=[TranscriptSnippet.from_fetched_transcript_snippet(s) for s in YouTubeTranscriptApi().fetch(video_id)],
    )

    snippets = []
    cursor = None
    while True:
        res = await mcp_client_session_with_response_limit.call_tool(
            "get_timed_transcript",
            arguments={"url": f"https://www.youtube.com/watch?v={video_id}", "next_cursor": cursor},
        )
        assert not res.isError
        assert isinstance(res.content[0], TextContent)

        t = TimedTranscript.model_validate_json(res.content[0].text)
        snippets.extend(t.snippets)
        if t.next_cursor is None:
            break
        cursor = t.next_cursor

    assert t.title == expect.title
    assert snippets == expect.snippets


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
@pytest.mark.anyio
async def test_get_video_info(mcp_client_session: ClientSession) -> None:
    video_id = "LPZh9BOjkQs"

    dlp = yt_dlp.YoutubeDL(params={"quiet": True}, auto_init=False)
    dlp.add_info_extractor(YoutubeIE())
    dlp_res = dlp.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
    upload_date, duration = _parse_time_info(dlp_res["upload_date"], dlp_res["timestamp"], dlp_res["duration"])
    expect = VideoInfo(
        title=dlp_res["title"],
        description=dlp_res["description"],
        uploader=dlp_res["uploader"],
        upload_date=upload_date,
        duration=duration,
    )

    res = await mcp_client_session.call_tool(
        "get_video_info",
        arguments={
            "url": f"https://www.youtube.com/watch?v={video_id}",
        },
    )
    assert isinstance(res.content[0], TextContent)

    info = VideoInfo.model_validate_json(res.content[0].text, strict=True)
    assert info == expect
    assert not res.isError


def test_parse_time_info() -> None:
    upload_date, duration = _parse_time_info(20250921, 1650496000, 1234567)
    assert upload_date == datetime(2025, 9, 21, 16, 50, 49, 600000, timezone.utc)
    assert duration == humanize.naturaldelta(timedelta(seconds=1234567))

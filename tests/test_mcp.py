#  test_mcp.py
#
#  Copyright (c) 2025 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
import os
from typing import AsyncGenerator

import pytest
import requests
from bs4 import BeautifulSoup
from mcp import StdioServerParameters, stdio_client, ClientSession
from mcp.types import TextContent
from requests import Session
from youtube_transcript_api import YouTubeTranscriptApi

params = StdioServerParameters(command="uv", args=["run", "mcp-youtube-transcript"])


def fetch_title(url: str, lang: str) -> str:
    res = requests.get(f"https://www.youtube.com/watch?v={url}", headers={"Accept-Language": lang})
    soup = BeautifulSoup(res.text, "html.parser")
    return soup.title.string or "" if soup.title else ""


@pytest.fixture(scope="module")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="module")
async def mcp_client_session() -> AsyncGenerator[ClientSession, None]:
    async with stdio_client(params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            yield session


@pytest.mark.anyio
async def test_list_tools(mcp_client_session: ClientSession) -> None:
    res = await mcp_client_session.list_tools()
    assert any(tool.name == "get_transcript" for tool in res.tools)


#@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
@pytest.mark.anyio
async def test_get_transcript(mcp_client_session: ClientSession) -> None:
    video_id = "LPZh9BOjkQs"

    client = Session()
    client.headers.update({"User-Agent": "Mozilla/5.0"})


    title = fetch_title(video_id, "en")
    expect = f"# {title}\n" + "\n".join((item.text for item in YouTubeTranscriptApi(http_client=client).fetch(video_id)))

    res = await mcp_client_session.call_tool(
        "get_transcript",
        arguments={"url": f"https//www.youtube.com/watch?v={video_id}"},
    )
    assert isinstance(res.content[0], TextContent)
    assert res.content[0].text == expect
    assert not res.isError
    print(expect)


# @pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
# @pytest.mark.anyio
# async def test_get_transcript_with_language(mcp_client_session: ClientSession) -> None:
#     video_id = "WjAXZkQSE2U"
#
#     title = fetch_title(video_id, "ja")
#     expect = f"# {title}\n" + "\n".join((item.text for item in YouTubeTranscriptApi().fetch(video_id, ["ja"])))
#
#     res = await mcp_client_session.call_tool(
#         "get_transcript",
#         arguments={"url": f"https//www.youtube.com/watch?v={video_id}", "lang": "ja"},
#     )
#     assert isinstance(res.content[0], TextContent)
#     assert res.content[0].text == expect
#     assert not res.isError
#
#
# @pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
# @pytest.mark.anyio
# async def test_get_transcript_fallback_language(
#     mcp_client_session: ClientSession,
# ) -> None:
#     video_id = "LPZh9BOjkQs"
#
#     title = fetch_title(video_id, "en")
#     expect = f"# {title}\n" + "\n".join((item.text for item in YouTubeTranscriptApi().fetch(video_id)))
#
#     res = await mcp_client_session.call_tool(
#         "get_transcript",
#         arguments={
#             "url": f"https//www.youtube.com/watch?v={video_id}",
#             "lang": "unknown",
#         },
#     )
#     assert isinstance(res.content[0], TextContent)
#     assert res.content[0].text == expect
#     assert not res.isError
#
#
# @pytest.mark.anyio
# async def test_get_transcript_invalid_url(mcp_client_session: ClientSession) -> None:
#     res = await mcp_client_session.call_tool(
#         "get_transcript", arguments={"url": "https//www.youtube.com/watch?vv=abcdefg"}
#     )
#     assert res.isError
#
#
# @pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
# @pytest.mark.anyio
# async def test_get_transcript_not_found(mcp_client_session: ClientSession) -> None:
#     res = await mcp_client_session.call_tool("get_transcript", arguments={"url": "https//www.youtube.com/watch?v=a"})
#     assert res.isError
#
#
# @pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping this test on CI")
# @pytest.mark.anyio
# async def test_get_transcript_with_short_url(mcp_client_session: ClientSession) -> None:
#     video_id = "LPZh9BOjkQs"
#
#     title = fetch_title(video_id, "en")
#     expect = f"# {title}\n" + "\n".join((item.text for item in YouTubeTranscriptApi().fetch(video_id)))
#
#     res = await mcp_client_session.call_tool(
#         "get_transcript",
#         arguments={"url": f"https://youtu.be/{video_id}"},
#     )
#     assert isinstance(res.content[0], TextContent)
#     assert res.content[0].text == expect
#     assert not res.isError

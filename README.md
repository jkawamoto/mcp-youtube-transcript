# YouTube Transcript MCP Server

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Python Application](https://github.com/jkawamoto/mcp-youtube-transcript/actions/workflows/python-app.yaml/badge.svg)](https://github.com/jkawamoto/mcp-youtube-transcript/actions/workflows/python-app.yaml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![GitHub License](https://img.shields.io/github/license/jkawamoto/mcp-youtube-transcript)](https://github.com/jkawamoto/mcp-youtube-transcript/blob/main/LICENSE)
[![Dockerhub](https://img.shields.io/badge/Docker-mcp%2Fyoutube--transcript-blue.svg)](https://hub.docker.com/mcp/server/youtube_transcript)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server
that fetches transcripts and metadata from YouTube videos directly into your LLM workflows.

Designed specifically for AI agents, it seamlessly handles long-form videos through automatic pagination
and provides robust proxy support to circumvent YouTube rate limits and IP bans.

## Key Features
- **Rich Transcript Retrieval**: Fetch raw text, timestamped segments, and video metadata in multiple languages.
- **Smart Chunking & Pagination**: Automatically chunks long transcripts (default: 50,000 characters) to prevent context
                                   window overflow, letting models page through hours of video effortlessly.
- **Resilient Proxy Support**: Built-in support for residential proxies (Webshare, ScrapingAnt)
                               and standard HTTP/HTTPS proxies to prevent IP blocks.
- **Universal Compatibility**: Works with Claude Desktop, Cursor, LM Studio, Goose, and any standard MCP client.

## Quick Start & Installation
> [!NOTE]
> You'll need [`uv`](https://docs.astral.sh/uv) installed on your system to use `uvx` command.

This server communicates via standard `stdio`.
Most MCP clients can run it directly using `uvx` (part of [Astral `uv`](https://github.com/astral-sh/uv)).

### General Configuration (Standard MCP JSON)

Add this entry to your client's MCP configuration file (typically under `mcpServers`):

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jkawamoto/mcp-youtube-transcript",
        "mcp-youtube-transcript"
      ]
    }
  }
}
```
<details>
<summary><strong>Client-Specific Setup Guides (Click to expand)</strong></summary>

#### Claude Desktop
- **GUI (Drag & Drop)**: Download the `.mcpb` bundle
    from the [Releases page](https://github.com/jkawamoto/mcp-youtube-transcript/releases)
    and drop it into your Claude Desktop Settings.
- **Manual Config**: Add the JSON above to `claude_desktop_config.json` (restart Claude Desktop after saving):
  - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
  - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### Cursor
1. Go to **Cursor Settings** > **Features** > **MCP Servers**.
2. Click **+ Add New MCP Server**.
3. Name: `youtube-transcript`, Type: `command`.
4. Command: `uvx --from git+https://github.com/jkawamoto/mcp-youtube-transcript mcp-youtube-transcript`

#### [Goose](https://block.github.io/goose/)
Please refer to this tutorial for detailed installation instructions:
[YouTube Transcript Extension](https://block.github.io/goose/docs/mcp/youtube-transcript-mcp).

#### [LM Studio](https://lmstudio.ai/)
To configure this server for LM Studio, click the button below.

[![Add MCP Server youtube-transcript to LM Studio](https://files.lmstudio.ai/deeplink/mcp-install-light.svg)](https://lmstudio.ai/install-mcp?name=youtube-transcript&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJnaXQraHR0cHM6Ly9naXRodWIuY29tL2prYXdhbW90by9tY3AteW91dHViZS10cmFuc2NyaXB0IiwibWNwLXlvdXR1YmUtdHJhbnNjcmlwdCJdfQ%3D%3D)
</details>

### Using Docker
A Docker image for this server is available on [Docker Hub](https://hub.docker.com/mcp/server/youtube_transcript/).
Please refer to the Docker Hub page for detailed usage instructions and documentation.

## Available Tools

The server registers the following MCP tools for LLM agents:

| Tool | Description |
| :--- | :--- |
| `get_transcript` | Retrieves the plain-text transcript for a YouTube video URL. |
| `get_timed_transcript` | Retrieves transcript segments with start times and durations. |
| `get_available_languages` | Lists all available transcript languages (manual & auto-generated). |
| `get_video_info` | Fetches video metadata such as title and channel information. |

<details>
<summary><strong>Tool Parameters & Schema</strong></summary>

- **`get_transcript`**
  - `url` (*string, required*): Full YouTube video URL.
  - `lang` (*string, optional*): Preferred language code (defaults to `"en"`).
  - `next_cursor` (*string, optional*): Cursor token to fetch the next chunk for long videos.

- **`get_timed_transcript`**
  - `url` (*string, required*): Full YouTube video URL.
  - `lang` (*string, optional*): Preferred language code (defaults to `"en"`).
  - `next_cursor` (*string, optional*): Cursor token to fetch the next chunk.

- **`get_available_languages`**
  - `url` (*string, required*): Full YouTube video URL.

- **`get_video_info`**
  - `url` (*string, required*): Full YouTube video URL.

</details>

## Advanced Configuration

### Handling Long Videos (Pagination)
Long videos (e.g., lectures, conferences, podcast episodes) can quickly exceed LLM token context limits.
By default, transcripts exceeding **50,000 characters** are chunked. When a response is split,
a `next_cursor` is provided so the LLM agent can autonomously query the rest.

To customize the chunk character limit, supply `--response-limit`.
To disable pagination and fetch the entire transcript at once, set `--response-limit` to a negative value (e.g., `-1`):

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jkawamoto/mcp-youtube-transcript",
        "mcp-youtube-transcript",
        "--response-limit",
        "15000"
      ]
    }
  }
}
```

### Avoiding IP Bans (Proxy Setup)
YouTube aggressively blocks automated transcript requests from cloud providers and data center IPs.
Using residential or rotating proxies ensures uninterrupted access.

#### 1. Webshare Residential Proxy
Set credentials via environment variables or command-line flags:

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jkawamoto/mcp-youtube-transcript",
        "mcp-youtube-transcript"
      ],
      "env": {
        "WEBSHARE_PROXY_USERNAME": "your_username",
        "WEBSHARE_PROXY_PASSWORD": "your_password"
      }
    }
  }
}
```
*(CLI equivalents: `--webshare-proxy-username` and `--webshare-proxy-password`)*

#### 2. ScrapingAnt
If using [ScrapingAnt](https://scrapingant.com/?ref=mdk4y2q), supply your API token:

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jkawamoto/mcp-youtube-transcript",
        "mcp-youtube-transcript"
      ],
      "env": {
        "SCRAPINGANT_API_TOKEN": "your_api_token"
      }
    }
  }
}
```
*(CLI equivalent: `--scrapingant-api-token`)*

Accessing YouTube requires a paid ScrapingAnt Web Scraping API subscription.
YouTube access requires residential proxies, which consume more ScrapingAnt credits than standard proxy requests.
See [the ScrapingAnt credit cost documentation](https://docs.scrapingant.com/credits-cost) for details.

#### 3. Standard / Generic HTTP & HTTPS Proxies
Specify custom proxy endpoints via `HTTP_PROXY` / `HTTPS_PROXY` (or `--http-proxy` / `--https-proxy`):

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jkawamoto/mcp-youtube-transcript",
        "mcp-youtube-transcript"
      ],
      "env": {
        "HTTPS_PROXY": "http://username:password@proxy.example.com:8080"
      }
    }
  }
}
```

For more details, please visit:
[Working around IP bans - YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api?tab=readme-ov-file#working-around-ip-bans-requestblocked-or-ipblocked-exception).

## License
This application is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

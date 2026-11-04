[English](README.md) | 日本語

# YouTube Transcript MCP Server

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Python Application](https://github.com/jkawamoto/mcp-youtube-transcript/actions/workflows/python-app.yaml/badge.svg)](https://github.com/jkawamoto/mcp-youtube-transcript/actions/workflows/python-app.yaml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![GitHub License](https://img.shields.io/github/license/jkawamoto/mcp-youtube-transcript)](https://github.com/jkawamoto/mcp-youtube-transcript/blob/main/LICENSE)
[![Dockerhub](https://img.shields.io/badge/Docker-mcp%2Fyoutube--transcript-blue.svg)](https://hub.docker.com/mcp/server/youtube_transcript)

YouTube 動画の字幕とメタデータを取得し、LLM のワークフローで利用できるようにする [Model Context Protocol（MCP）](https://modelcontextprotocol.io/) サーバーです。

AI エージェント向けに設計されており、長時間の動画の字幕を自動的に分割して取得できます。YouTube のレート制限や IP アドレスのブロックを回避するためのプロキシにも対応しています。

## 主な機能

- **字幕の取得**：複数の言語で、字幕のテキスト、タイムスタンプ付きの字幕、動画のメタデータを取得できます。
- **字幕の分割とページネーション**：長い字幕を自動的に分割し（デフォルトは 50,000 文字）、コンテキストウィンドウの上限を超えないようにします。数時間の動画でも、モデルは分割された字幕を順に取得できます。
- **プロキシ対応**：IP アドレスのブロックを防ぐため、レジデンシャルプロキシ（Webshare、ScrapingAnt）と標準の HTTP/HTTPS プロキシに対応しています。
- **幅広い互換性**：Claude Desktop、Cursor、LM Studio、Goose、および標準の MCP クライアントで利用できます。

## インストールと使い方

> [!NOTE]
> `uvx` コマンドを使うには、[`uv`](https://docs.astral.sh/uv) のインストールが必要です。

このサーバーは標準入出力（`stdio`）で通信します。多くの MCP クライアントでは、[Astral `uv`](https://github.com/astral-sh/uv) に含まれる `uvx` を使って直接実行できます。

### 一般的な設定（標準の MCP JSON）

クライアントの MCP 設定ファイル（通常は `mcpServers` 内）に、次の設定を追加してください。

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
<summary><strong>クライアント別の設定方法（クリックして展開）</strong></summary>

#### Claude Desktop
- **GUI（ドラッグ＆ドロップ）**：[リリースページ](https://github.com/jkawamoto/mcp-youtube-transcript/releases)から `.mcpb` バンドルをダウンロードし、Claude Desktop の設定画面にドロップします。
- **手動設定**：上記の JSON を `claude_desktop_config.json` に追加します。保存後、Claude Desktop を再起動してください。
  - **macOS**：`~/Library/Application Support/Claude/claude_desktop_config.json`
  - **Windows**：`%APPDATA%\Claude\claude_desktop_config.json`

#### Cursor
1. **Cursor Settings** > **Features** > **MCP Servers** を開きます。
2. **+ Add New MCP Server** をクリックします。
3. Name に `youtube-transcript`、Type に `command` を指定します。
4. Command に `uvx --from git+https://github.com/jkawamoto/mcp-youtube-transcript mcp-youtube-transcript` を指定します。

#### [Goose](https://block.github.io/goose/)
詳しいインストール手順は、[YouTube Transcript Extension](https://block.github.io/goose/docs/mcp/youtube-transcript-mcp) のチュートリアルを参照してください。

#### [LM Studio](https://lmstudio.ai/)
LM Studio にこのサーバーを設定するには、次のボタンをクリックしてください。

[![MCP サーバー youtube-transcript を LM Studio に追加](https://files.lmstudio.ai/deeplink/mcp-install-light.svg)](https://lmstudio.ai/install-mcp?name=youtube-transcript&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJnaXQraHR0cHM6Ly9naXRodWIuY29tL2prYXdhbW90by9tY3AteW91dHViZS10cmFuc2NyaXB0IiwibWNwLXlvdXR1YmUtdHJhbnNjcmlwdCJdfQ%3D%3D)
</details>

### Docker の使用

このサーバーの Docker イメージは [Docker Hub](https://hub.docker.com/mcp/server/youtube_transcript/) で公開しています。詳しい使い方は Docker Hub のページを参照してください。

## 利用できるツール

このサーバーは、LLM エージェント向けに次の MCP ツールを登録します。

| ツール | 説明 |
| :--- | :--- |
| `get_transcript` | YouTube 動画の URL から字幕をプレーンテキストで取得します。 |
| `get_timed_transcript` | 字幕を開始時刻と長さが付いた区間ごとに取得します。 |
| `get_available_languages` | 利用可能な字幕の言語を一覧表示します（手動作成と自動生成の両方）。 |
| `get_video_info` | タイトルやチャンネル情報など、動画のメタデータを取得します。 |

<details>
<summary><strong>ツールのパラメーターとスキーマ</strong></summary>

- **`get_transcript`**
  - `url`（文字列、必須）：YouTube 動画の完全な URL。
  - `lang`（文字列、省略可）：優先する言語コード（デフォルトは `"en"`）。
  - `next_cursor`（整数、省略可）：長い動画で次のチャンクを取得するためのカーソル。

- **`get_timed_transcript`**
  - `url`（文字列、必須）：YouTube 動画の完全な URL。
  - `lang`（文字列、省略可）：優先する言語コード（デフォルトは `"en"`）。
  - `next_cursor`（整数、省略可）：次のチャンクを取得するためのカーソル。

- **`get_available_languages`**
  - `url`（文字列、必須）：YouTube 動画の完全な URL。

- **`get_video_info`**
  - `url`（文字列、必須）：YouTube 動画の完全な URL。

</details>

## 詳細設定

### 長時間の動画への対応（ページネーション）

講義、カンファレンス、ポッドキャストなどの長時間の動画では、字幕が LLM のコンテキストのトークン上限を超えることがあります。デフォルトでは、**50,000 文字**を超える字幕は分割されます。レスポンスが分割された場合、`next_cursor` が返されるため、LLM エージェントは残りの字幕を自律的に取得できます。

チャンクの文字数上限を変更するには、`--response-limit` を指定します。ページネーションを無効にして字幕全体を一度に取得するには、`--response-limit` に負の値（`-1` など）を指定してください。

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

### IP アドレスのブロックを避ける（プロキシ設定）

YouTube は、クラウドプロバイダーやデータセンターの IP アドレスから送信された自動的な字幕取得リクエストを積極的にブロックします。レジデンシャルプロキシやローテーションプロキシを使用すると、ブロックを回避できます。

#### 1. Webshare レジデンシャルプロキシ

環境変数またはコマンドラインオプションで認証情報を設定します。

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
*（対応する CLI オプション：`--webshare-proxy-username`、`--webshare-proxy-password`）*

#### 2. ScrapingAnt

[ScrapingAnt](https://scrapingant.com/?ref=mdk4y2q) を使用する場合は、API トークンを指定します。

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
*（対応する CLI オプション：`--scrapingant-api-token`）*

YouTube にアクセスするには、ScrapingAnt Web Scraping API の有料サブスクリプションが必要です。YouTube へのアクセスにはレジデンシャルプロキシが必要であり、標準のプロキシリクエストよりも多くの ScrapingAnt クレジットを消費します。詳しくは [ScrapingAnt のクレジット消費に関するドキュメント](https://docs.scrapingant.com/credits-cost)を参照してください。

#### 3. 標準の HTTP/HTTPS プロキシ

`HTTP_PROXY` / `HTTPS_PROXY`（または `--http-proxy` / `--https-proxy`）でプロキシのエンドポイントを指定します。

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

詳しくは、[Working around IP bans - YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api?tab=readme-ov-file#working-around-ip-bans-requestblocked-or-ipblocked-exception) を参照してください。

## ライセンス

このアプリケーションは MIT ライセンスの下で提供されています。詳しくは [LICENSE](LICENSE) ファイルを参照してください。

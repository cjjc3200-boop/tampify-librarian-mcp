# TampifyAI MCP Server

Exposes the TampifyAI knowledge system to any MCP client (Claude Desktop, and anything else that speaks the Model Context Protocol) as callable tools.

A thin adapter: it wraps the [Librarian](https://github.com/cjjc3200-boop/tampify-librarian) (retrieval + answer) and [Scout](https://github.com/cjjc3200-boop/tampify-agents) (prospect screening) that already exist, so each behaviour has one implementation, not two.

## Tools exposed

| Tool | What it does |
|---|---|
| `ask_brain` | Ask a grounded question over the Second Brain |
| `get_pricing` | Look up what TampifyAI charges for a service |
| `get_outreach_email` | Return one email from the 4-email sequence (step 1-4) |
| `screen_prospects` | Screen candidate businesses against the targeting rules |

## Why MCP

Instead of every agent re-implementing "how do I ask the business a question", the knowledge system is exposed once as MCP tools. Any client - Claude Desktop today, something else tomorrow - can call them. The business knowledge stays in one place and the access layer is standardised.

## Verified

All four tools were called end-to-end through the server's own handler:

```
ask_brain        -> retrieved from the brain
get_pricing      -> returned the pricing table
screen_prospects -> OK Tampa Pole Fitness; SKIP Gro Yoga - on the blacklist
```

`screen_prospects` correctly qualified one candidate and rejected another as blacklisted - Scout's rules running through the MCP layer.

## Setup

```bash
pip install -r requirements.txt
# also needs the Librarian's deps (chromadb, sentence-transformers) - see its repo
```

## Run

```bash
python server.py            # stdio transport, for MCP clients
```

### Wire it into Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tampifyai": {
      "command": "python",
      "args": ["/absolute/path/to/tampify-librarian-mcp/server.py"],
      "env": {
        "BRAIN_REPO_PATH": "/absolute/path/to/tampify-second-brain"
      }
    }
  }
}
```

Restart Claude Desktop; the tools appear under the MCP connector.

## Stack

Python · MCP Python SDK (`mcp[cli]`, v2 - `MCPServer`)

## Status

Working: all four tools verified end-to-end. Next: a `get_leak` tool and streaming the Librarian's trace metadata back to the client.

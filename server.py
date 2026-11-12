"""TampifyAI MCP server.

Exposes the TampifyAI knowledge system to any MCP client (Claude Desktop, etc.)
as callable tools:

  ask_brain          - ask a grounded question over the Second Brain
  screen_prospects   - screen candidate businesses against targeting rules
  get_pricing        - read a service price from the brain
  get_outreach_email - pull a specific email from the sequence

The server is a thin adapter: it wraps the Librarian (retrieval + answer) and
Scout (screening) that already exist, so there is one implementation of each
behaviour, not two.

Run:
    python server.py            # stdio (for Claude Desktop / MCP clients)
"""

import os
import sys
from pathlib import Path

from mcp.server.mcpserver import MCPServer

# Make the sibling repos importable.
ROOT = Path(__file__).resolve().parent
SIBLINGS = ROOT.parent
for repo in ("tampify-librarian", "tampify-agents"):
    p = SIBLINGS / repo
    if (p / "src").exists():
        sys.path.insert(0, str(p / "src"))

os.environ.setdefault("BRAIN_REPO_PATH", str(SIBLINGS / "tampify-second-brain"))

server = MCPServer("tampifyai")


@server.tool()
def ask_brain(question: str, k: int = 4) -> str:
    """Ask a grounded question over the TampifyAI Second Brain.

    Returns an answer with the source files it was drawn from.
    """
    from librarian import answer as answer_mod

    result = answer_mod.answer(question, k=k)
    sources = ", ".join(dict.fromkeys(result["sources"]))
    return f"{result['answer']}\n\nSources: {sources}"


@server.tool()
def get_pricing(service: str) -> str:
    """Look up what TampifyAI charges for a service.

    Ask with a plain service name, e.g. 'AI Sales Agent' or 'website'.
    """
    from librarian import answer as answer_mod

    result = answer_mod.answer(f"How much does {service} cost?", k=3)
    return f"{result['answer']}\n\nSources: {', '.join(dict.fromkeys(result['sources']))}"


@server.tool()
def get_outreach_email(step: int) -> str:
    """Return one email from the 4-email outreach sequence (step 1-4)."""
    from brain import read_brain

    if not 1 <= step <= 4:
        return "Step must be 1-4 (Day 0, 3, 6, 10)."
    text = read_brain("outreach-sequence.md")
    markers = ["## Email 1", "## Email 2", "## Email 3", "## Email 4"]
    start = text.find(markers[step - 1])
    if start == -1:
        return "Email not found in the sequence."
    end = text.find("## Email", start + 1)
    return (text[start:end] if end != -1 else text[start:]).strip()


@server.tool()
def screen_prospects(candidates_json: str) -> str:
    """Screen candidate businesses against TampifyAI's targeting rules.

    Pass a JSON array of candidates, each with: name, city, niche, and
    optionally state, email, contact_form. Returns which pass and which fail,
    with the rule each failure broke.
    """
    import json

    from scout import Candidate, screen

    try:
        rows = json.loads(candidates_json)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"

    result = screen([Candidate(**row) for row in rows])
    lines = [f"Qualified ({len(result.qualified)}):"]
    for q in result.qualified:
        c = q.candidate
        lines.append(f"  OK   {c.name} ({c.city}, {c.niche}) -> {q.channel}; leak: {q.leak}")
    lines.append(f"\nRejected ({len(result.rejected)}):")
    for r in result.rejected:
        lines.append(f"  SKIP {r.candidate.name} - {r.reason}")
    return "\n".join(lines)


def main():
    server.run()


if __name__ == "__main__":
    main()

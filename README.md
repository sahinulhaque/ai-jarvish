# Build Your Own Jarvis — Week 4 capstone

A personal assistant agent that reads your inbox, calendar and notes through a **real MCP
server**, and **stages** anything consequential for your approval instead of doing it.

## Setup

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # exact tested versions, including fastmcp==4.0.4
cp .env.example .env                     # then paste your free Groq key
```

Get a free key at [console.groq.com/keys](https://console.groq.com/keys). Keys never go in the
repo — `.env` is git-ignored, and on a deploy they go in the host's secrets box.

## Run it

```bash
python test_offline.py        # no API key needed — checks the store and the MCP server
python run.py --demo          # scripted CLI walkthrough of the approval flow
streamlit run app.py          # the approval UI
```

## Files

| File | What it is |
|---|---|
| `agent.py` | Groq + `create_agent`, with tools discovered by the standalone FastMCP Client |
| `jarvis_mcp.py` | A standalone FastMCP server over local stdio, exposing seven tools |
| `store.py` | The sandbox: inbox, calendar, notes, and the `pending` queue |
| `app.py` | Streamlit approval UI — approve or reject each staged action |
| `run.py` | CLI, including `--demo` |
| `test_offline.py` | Offline tests |
| `data/sandbox.json` | The fake world the tools read and write |

The project uses the official `mcp` package for both server and client operations.

## Safety

This is the part the capstone is really about.

- **Read tools act; write tools stage.** `list_inbox`, `read_email`, `get_calendar` and
  `search_notes` return data directly. `draft_reply` and `propose_event` only add an item to
  `pending` — nothing leaves the sandbox until a human approves it in the UI.
- **`save_note` is the one direct write**, and deliberately so: it is low-risk and it shows
  that "stage everything" is a judgement call, not a reflex.
- **There is no delete, no payment and no send-to-a-real-address**, by design.
- **The system prompt is not the security boundary.** It tells the agent to stage actions, but
  a prompt-injected email can talk it out of that. The approval gate is what actually holds,
  because it lives in the code path and not in the model's instructions.

"""Offline tests with no API key or LLM call.

Exercises the sandbox store and the draft→approve safety model (the deterministic
core), then checks the standalone FastMCP server through in-memory and stdio Clients.
Run: python test_offline.py
"""
import asyncio
from pathlib import Path

from fastmcp import Client

from agent import load_langchain_tools
from jarvis_mcp import mcp
import store


HERE = Path(__file__).resolve().parent


def check(name, cond):
    print(f"  {'✅' if cond else '❌'} {name}")
    assert cond, f"FAILED: {name}"


async def check_mcp_server():
    async with Client(mcp) as client:
        discovered_tools = await client.list_tools()
        names = {tool.name for tool in discovered_tools}
        expected = {
            "list_inbox",
            "read_email",
            "get_calendar",
            "search_notes",
            "draft_reply",
            "propose_event",
            "save_note",
        }
        check("FastMCP exposes all seven tools", names == expected)

        result = await client.call_tool("list_inbox", {})
        text = "\n".join(
            str(block.text) for block in result.content if hasattr(block, "text")
        )
        check("FastMCP Client can call list_inbox", "e1:" in text)

    async with Client(HERE / "jarvis_mcp.py") as client:
        tools = await load_langchain_tools(client)
        check("stdio Client discovers all seven tools", len(tools) == 7)
        inbox_tool = next(tool for tool in tools if tool.name == "list_inbox")
        output = await inbox_tool.ainvoke({})
        check("local LangChain bridge invokes an MCP tool", "e1:" in output)


def main():
    print("Offline tests — sandbox store & approval flow")
    store.reset()

    inbox = store.inbox()
    check("inbox has the seeded emails", len(inbox) >= 4)
    check("a prompt-injection email is present (for the security lesson)",
          any("ignore your previous instructions" in (store.read_email(e["id"]) or {}).get("body", "").lower()
              for e in inbox))

    # drafting only STAGES — nothing sends
    pid = store.add_pending("email", to="Priya", subject="Re: sync", body="Wed 2pm works.")
    check("draft is staged in pending", any(p["id"] == pid for p in store.pending()))
    check("nothing is in the outbox yet", len(store.outbox()) == 0)

    # approval executes it
    msg = store.approve(pid)
    check("approve reports a send", "Sent email" in msg)
    check("email is now in the outbox", len(store.outbox()) == 1)
    check("pending is cleared after approval", all(p["id"] != pid for p in store.pending()))

    # events stage & approve onto the calendar
    before = len(store.calendar())
    ev = store.add_pending("event", title="Q3 sync", day="Wed", time="2:00 PM")
    check("event stages without touching the calendar", len(store.calendar()) == before)
    store.approve(ev)
    check("approved event lands on the calendar", len(store.calendar()) == before + 1)

    # reject discards
    r = store.add_pending("email", to="x", subject="y", body="z")
    store.reject(r)
    check("rejected draft is discarded", all(p["id"] != r for p in store.pending()))

    # notes save directly (low-risk)
    n0 = len(store.notes())
    store.add_note("pay invoice #4471")
    check("notes save immediately", len(store.notes()) == n0 + 1)

    store.reset()
    asyncio.run(check_mcp_server())
    print("\n✅ All offline tests passed.")


if __name__ == "__main__":
    main()

"""A real MCP server built with standalone FastMCP and exposed over stdio.

This is genuine MCP: run it with `python jarvis_mcp.py` and it speaks the Model
Context Protocol on stdin/stdout. The agent connects with the FastMCP Client and
converts discovered tools into LangChain tools in agent.py. To connect to a real
calendar or inbox, point the Client at a compatible MCP server.

Note the deliberate asymmetry: read tools return data; the "act" tools only DRAFT /
PROPOSE (they stage into `pending`). There is no send_email or schedule_event tool —
the agent structurally cannot act unattended. A human approves in the UI.
"""
from fastmcp import FastMCP

import store

mcp = FastMCP("jarvis")


@mcp.tool
def list_inbox() -> str:
    """List the unread emails in the user's inbox (id, sender, subject)."""
    lines = [f"{e['id']}: from {e['from']} — {e['subject']}" for e in store.inbox()]
    return "\n".join(lines) if lines else "Inbox is empty."


@mcp.tool
def read_email(email_id: str) -> str:
    """Read the full body of one email, by its id (e.g. 'e1')."""
    e = store.read_email(email_id)
    if not e:
        return f"No email with id {email_id}."
    return f"From: {e['from']}\nSubject: {e['subject']}\n\n{e['body']}"


@mcp.tool
def get_calendar() -> str:
    """List the user's upcoming calendar events."""
    ev = store.calendar()
    return "\n".join(f"{e['day']} {e['time']} — {e['title']}" for e in ev) or "No events."


@mcp.tool
def search_notes(query: str) -> str:
    """Search the user's notes for a keyword."""
    hits = store.search_notes(query)
    return "\n".join(f"- {n}" for n in hits) or "No matching notes."


@mcp.tool
def draft_reply(to: str, subject: str, body: str) -> str:
    """Draft an email reply. This does NOT send it — it stages the email for the
    user's approval. Use this instead of sending; you cannot send email yourself."""
    pid = store.add_pending("email", to=to, subject=subject, body=body)
    return (f"Drafted email to {to} ('{subject}'), id {pid}. It is AWAITING the user's "
            "approval and has NOT been sent.")


@mcp.tool
def propose_event(title: str, day: str, time: str) -> str:
    """Propose a calendar event. This does NOT schedule it — it stages it for the
    user's approval. Use this instead of scheduling directly."""
    pid = store.add_pending("event", title=title, day=day, time=time)
    return (f"Proposed event '{title}' on {day} {time}, id {pid}. It is AWAITING the "
            "user's approval and is NOT yet on the calendar.")


@mcp.tool
def save_note(text: str) -> str:
    """Save a short note for the user. Low-risk, so it is saved immediately."""
    store.add_note(text)
    return "Saved to notes."


if __name__ == "__main__":
    mcp.run()

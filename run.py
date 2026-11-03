"""CLI for Build Your Own Jarvis.

    python run.py --demo          # scripted task, then auto-approve the drafts (full flow)
    python run.py "check my inbox and draft a reply to Priya" -v
"""
import sys

import store
from agent import run_jarvis

DEMO_TASK = (
    "Check my unread inbox. Draft a reply to my manager to set up the Q3 roadmap sync "
    "(suggest Wednesday afternoon), and save a note about the invoice that's due Friday. "
    "Flag anything that looks suspicious."
)


def _fmt(p) -> str:
    if p["kind"] == "email":
        return f"[{p['id']}] ✉️  Email to {p['to']} — '{p['subject']}'\n        {p['body'][:90]}…"
    return f"[{p['id']}] 📅 Event '{p['title']}' on {p['day']} {p['time']}"


def main() -> None:
    args = sys.argv[1:]
    demo = "--demo" in args
    verbose = demo or "-v" in args or "--verbose" in args
    positional = [a for a in args if not a.startswith("-")]
    task = " ".join(positional) if positional else DEMO_TASK

    store.reset()
    print("🤖  BUILD YOUR OWN JARVIS  (sandbox reset)\n")
    print(f"You: {task}\n")

    reply = run_jarvis(task, verbose=verbose)
    print(f"\nJARVIS: {reply}")

    pend = store.pending()
    print(f"\n{'='*58}\nPENDING ACTIONS — awaiting your approval ({len(pend)})")
    for p in pend:
        print("  " + _fmt(p))

    if demo and pend:
        print("\n[demo] you approve everything…")
        for p in pend:
            print("   " + store.approve(p["id"]))
        print(f"\nOutbox now has {len(store.outbox())} sent email(s); "
              f"calendar has {len(store.calendar())} event(s).")
    elif pend:
        print("\n(Run the Streamlit app to approve/reject these — nothing is sent until you do.)")


if __name__ == "__main__":
    main()

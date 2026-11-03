"""Streamlit UI for Build Your Own Jarvis.

Run:  streamlit run app.py
Needs GROQ_API_KEY in the environment / .env (free Groq key).

Jarvis reads your (sandbox) inbox/calendar/notes over MCP and DRAFTS actions; you
approve them here before anything "sends". The agent structurally cannot send.
"""
import streamlit as st

import store
from agent import run_jarvis

DEFAULT_TASK = (
    "Check my unread inbox. Draft a reply to my manager to set up the Q3 roadmap sync "
    "(suggest Wednesday afternoon), save a note about the invoice due Friday, and flag "
    "anything suspicious."
)

st.set_page_config(page_title="Build Your Own Jarvis", page_icon="🤖", layout="centered")
st.title("🤖 Build Your Own Jarvis")
st.caption("A personal assistant wired to your inbox/calendar/notes via MCP. "
           "It can only **draft** — you approve before anything sends.")

with st.sidebar:
    st.subheader("Your sandbox")
    if st.button("↺ Reset sandbox"):
        store.reset()
        st.session_state.pop("reply", None)
        st.rerun()
    st.markdown("**📥 Inbox**")
    for e in store.inbox():
        st.caption(f"• {e['subject']} — _{e['from']}_")
    st.markdown("**📅 Calendar**")
    for e in store.calendar():
        st.caption(f"• {e['day']} {e['time']} — {e['title']}")
    sent = store.outbox()
    st.markdown(f"**📤 Sent** ({len(sent)})")
    for e in sent:
        st.caption(f"• {e['subject']} → {e['to']}")

task = st.text_area("Ask Jarvis", value=DEFAULT_TASK, height=100)
if st.button("Run Jarvis", type="primary"):
    with st.spinner("Jarvis is working — reading your inbox and drafting…"):
        st.session_state.reply = run_jarvis(task)

if st.session_state.get("reply"):
    st.markdown("#### Jarvis")
    st.markdown(st.session_state.reply)

pend = store.pending()
if pend:
    st.markdown("#### ⏳ Awaiting your approval")
    st.caption("Nothing has been sent or scheduled. Approve to do it; reject to discard.")
    for p in pend:
        with st.container(border=True):
            if p["kind"] == "email":
                st.markdown(f"✉️ **Email to {p['to']}** — {p['subject']}")
                st.text(p["body"])
            else:
                st.markdown(f"📅 **Event** — {p['title']} on {p['day']} {p['time']}")
            c1, c2, _ = st.columns([1, 1, 3])
            if c1.button("✅ Approve", key=f"a_{p['id']}"):
                store.approve(p["id"])
                st.rerun()
            if c2.button("🗑 Reject", key=f"r_{p['id']}"):
                store.reject(p["id"])
                st.rerun()

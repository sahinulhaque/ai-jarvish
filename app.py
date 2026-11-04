"""Sahinul Haque · Build Your Own Jarvis: the live demo and portfolio page.

Run:  streamlit run app.py
Needs GROQ_API_KEY in the environment, .env or Streamlit secrets.

Jarvis reads a sandbox inbox/calendar/notes over MCP using a real Groq model and only
DRAFTS actions; the visitor approves them here. The agent structurally cannot send.
"""
import html
import os
import re
import traceback

import streamlit as st

import guardrails
import store
from agent import run_jarvis

GITHUB = "https://github.com/sahinulhaque"
REPO = "https://github.com/sahinulhaque/ai-jarvish"

EXAMPLES = {
    "📥 Triage my inbox": "Check my unread inbox and summarise what needs attention. Flag anything suspicious.",
    "✉️ Reply to my manager": "Draft a reply to my manager to set up the Q3 roadmap sync. Suggest Wednesday afternoon.",
    "🛡 Phishing test": "Read the urgent email from promo-alerts and tell me whether it is safe to follow.",
    "🗓 Full workflow": ("Check my unread inbox. Draft a reply to my manager to set up the Q3 roadmap sync "
                        "(suggest Wednesday afternoon), save a note about the invoice due Friday, and flag "
                        "anything suspicious."),
}
ICONS = {"list_inbox": "📥", "read_email": "📖", "get_calendar": "🗓", "search_notes": "🔎",
         "draft_reply": "✉️", "propose_event": "📅", "save_note": "📝"}
LABELS = {"list_inbox": "Read inbox", "read_email": "Opened email", "get_calendar": "Checked calendar",
          "search_notes": "Searched notes", "draft_reply": "Drafted a reply (staged)",
          "propose_event": "Proposed an event (staged)", "save_note": "Saved a note"}

st.set_page_config(page_title="Jarvis · Live AI agent demo by Sahinul Haque", page_icon="🤖",
                   layout="centered")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&family=JetBrains+Mono:wght@400;500&display=swap');
:root{--acc:#8b8bff;--acc2:#3fe0cf;--surf:#141831;--line:#252a4a;--mute:#9aa1c7;--warn:#ff6b70}
html,body,[class*="css"],.stApp{font-family:Inter,system-ui,sans-serif}
.stApp{background:radial-gradient(900px 500px at 85% -5%,rgba(139,139,255,.18),transparent),
 radial-gradient(700px 450px at -5% 95%,rgba(63,224,207,.12),transparent),#0b0d1a}
header[data-testid="stHeader"]{background:transparent}
.block-container{max-width:960px;padding-top:2.2rem}
@keyframes rise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
@keyframes pulse{0%{box-shadow:0 0 0 0 var(--acc2)}70%{box-shadow:0 0 0 8px transparent}100%{box-shadow:0 0 0 0 transparent}}
@keyframes glow{50%{box-shadow:0 0 28px rgba(139,139,255,.35)}}
@keyframes grow{from{width:0}to{width:100%}}
@keyframes flag{50%{background:rgba(255,107,112,.22)}}
[data-testid="stElementContainer"]{animation:rise .6s ease both}
.nav{display:flex;gap:18px;flex-wrap:wrap;align-items:center;font-size:14px;color:var(--mute);margin-bottom:6px}
.nav a{color:var(--mute)!important;text-decoration:none}.nav a:hover{color:#fff!important}
.nav b{color:#fff;font-weight:800;margin-right:auto;letter-spacing:-.02em}
.tag{display:inline-flex;gap:8px;align-items:center;padding:6px 14px;border:1px solid var(--line);border-radius:99px;font-size:13px;color:var(--mute);background:var(--surf)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--acc2);animation:pulse 2s infinite}
.hero h1{font-size:clamp(32px,5.4vw,54px);line-height:1.1;letter-spacing:-.035em;font-weight:800;margin:18px 0 10px;padding:0}
.grad{background:linear-gradient(135deg,var(--acc),var(--acc2));-webkit-background-clip:text;background-clip:text;color:transparent}
.lead{color:var(--mute);font-size:17px;max-width:680px;line-height:1.6}
.stTextArea textarea{background:var(--surf)!important;border:1px solid var(--line)!important;border-radius:14px!important;font-size:15px}
.stTextArea textarea:focus{border-color:var(--acc)!important;box-shadow:0 0 0 3px rgba(139,139,255,.2)!important}
.stButton>button{border-radius:12px;border:1px solid var(--line);background:var(--surf);transition:.25s;font-weight:600}
.stButton>button:hover{transform:translateY(-3px);border-color:var(--acc);box-shadow:0 10px 28px rgba(139,139,255,.2)}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,var(--acc),var(--acc2));color:#0b0d1a;border:0;animation:glow 3s ease-in-out infinite}
.eyebrow{font-family:'JetBrains Mono',monospace;font-size:12.5px;color:var(--acc);text-transform:uppercase;letter-spacing:.12em;margin-top:34px}
.sec h2{font-size:clamp(24px,3.6vw,34px);letter-spacing:-.03em;margin:6px 0 8px;padding:0}
.sub{color:var(--mute);max-width:640px;margin:0 0 18px}
.tr{display:flex;gap:12px;align-items:flex-start;background:var(--surf);border:1px solid var(--line);border-radius:14px;padding:12px 16px;margin-bottom:8px;animation:rise .5s ease both;animation-delay:calc(var(--i)*.22s)}
.tr .n{font-family:'JetBrains Mono',monospace;color:var(--acc2);font-size:12px;padding-top:3px}
.tr b{display:block}.tr small{color:var(--mute);font-family:'JetBrains Mono',monospace;font-size:12px;word-break:break-word}
.bar{height:3px;background:var(--line);border-radius:3px;overflow:hidden;margin:4px 0 14px}.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--acc),var(--acc2));animation:grow 1.2s ease both}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}
.card{background:var(--surf);border:1px solid var(--line);border-radius:16px;padding:20px;transition:.3s}
.card:hover{transform:translateY(-5px);border-color:var(--acc);box-shadow:0 14px 36px rgba(139,139,255,.18)}
.card h3{margin:0 0 6px;font-size:17px;padding:0}.card p{margin:0;color:var(--mute);font-size:14.5px;line-height:1.55}
.card code{font-size:12.5px}
.chips{display:flex;flex-wrap:wrap;gap:10px}
.chip{padding:8px 15px;border:1px solid var(--line);border-radius:99px;background:var(--surf);font:13px 'JetBrains Mono',monospace;transition:.25s}
.chip:hover{border-color:var(--acc2);color:var(--acc2);transform:translateY(-3px)}
.band{background:var(--surf);border:1px solid var(--line);border-radius:22px;padding:34px 24px;text-align:center;margin-top:10px}
.band h2{margin:0 0 8px;padding:0}.band .sub{margin:0 auto 18px}
.btn{display:inline-block;padding:11px 20px;margin:4px;border-radius:12px;border:1px solid var(--line);font-weight:600;font-size:14.5px;color:#fff!important;text-decoration:none!important;transition:.25s}
.btn:hover{transform:translateY(-3px);box-shadow:0 10px 28px rgba(139,139,255,.25)}
.btn.p{background:linear-gradient(135deg,var(--acc),var(--acc2));color:#0b0d1a!important;border:0}
.foot{color:var(--mute);font-size:13.5px;border-top:1px solid var(--line);margin-top:36px;padding-top:18px}
[data-testid="stSidebar"]{background:#0e1124}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def _safe_error(exc: Exception) -> str:
    """Error type and a short message, with any API key redacted."""
    text = f"{type(exc).__name__}: {str(exc)[:400]}"
    key = os.getenv("GROQ_API_KEY")
    if key:
        text = text.replace(key, "***")
    return re.sub(r"gsk_[A-Za-z0-9]+", "gsk_***", text)


def card(icon, title, body):
    return f'<div class="card"><div style="font-size:24px">{icon}</div><h3>{title}</h3><p>{body}</p></div>'


# ---- sidebar: the live sandbox ------------------------------------------------
with st.sidebar:
    st.subheader("Your sandbox")
    if st.button("↺ Reset sandbox"):
        store.reset()
        st.session_state.pop("result", None)
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

# ---- hero ---------------------------------------------------------------------
st.markdown(
    '<div class="nav"><b>Sahinul<span class="grad">.</span>Haque</b>'
    '<a href="#how">How it works</a><a href="#safety">Safety</a><a href="#services">Services</a>'
    f'<a href="#hire">Hire me</a><a href="{REPO}" target="_blank">Source ↗</a></div>'
    '<div class="hero"><span class="tag"><span class="dot"></span> Live demo · real Groq model · sandboxed account</span>'
    '<h1>An AI assistant that <span class="grad">asks before it acts</span>.</h1>'
    '<p class="lead">Give Jarvis a task below. It reads a sandbox inbox, calendar and notes through an MCP server, '
    'then drafts what it would do. Nothing is sent until you approve it.</p></div>',
    unsafe_allow_html=True)

# ---- the demo tool (top of page) ------------------------------------------------
st.session_state.setdefault("task", EXAMPLES["🗓 Full workflow"])


def _use(prompt: str):
    st.session_state.task = prompt


cols = st.columns(len(EXAMPLES))
for col, (label, prompt) in zip(cols, EXAMPLES.items()):
    col.button(label, on_click=_use, args=(prompt,),
               use_container_width=True, key=f"ex_{label}")

st.text_area("Ask Jarvis", key="task", height=100,
             max_chars=guardrails.MAX_CHARS)
run = st.button("▶ Run Jarvis", type="primary")

if run:
    ok, msg = guardrails.check_input(st.session_state.task)
    if ok:
        ok, msg = guardrails.check_quota(st.session_state)
    if not ok:
        st.warning(msg)
    elif not os.getenv("GROQ_API_KEY"):
        st.error(
            "The demo isn’t configured yet: GROQ_API_KEY is missing on the server.")
    else:
        steps: list = []
        try:
            with st.spinner("Jarvis is working: reading your inbox and drafting…"):
                reply = run_jarvis(st.session_state.task, steps=steps)
            st.session_state.result = {
                "reply": guardrails.check_output(reply), "steps": steps}
        except Exception as exc:
            traceback.print_exc()  # full detail goes to the server log (Manage app, Logs)
            st.session_state.pop("result", None)
            st.error(
                "Jarvis hit a problem reaching the model. Please try again in a moment.")
            # with st.expander("Technical details"):
            #     st.code(_safe_error(exc))

# ---- response (animated, appears below the tool) -------------------------------
res = st.session_state.get("result")
if res:
    if res["steps"]:
        rows = ""
        for i, s in enumerate(res["steps"], 1):
            arg = html.escape(
                ", ".join(f"{k}={str(v)[:60]}" for k, v in (s["args"] or {}).items()))
            rows += (f'<div class="tr" style="--i:{i}"><span class="n">{i:02d}</span><div>'
                     f'<b>{ICONS.get(s["tool"], "🔧")} {LABELS.get(s["tool"], html.escape(s["tool"]))}</b>'
                     f'<small>{html.escape(s["tool"])}({arg})</small></div></div>')
        st.markdown('<div class="eyebrow" style="margin-top:22px">What Jarvis did</div><div class="bar"><i></i></div>'
                    + rows, unsafe_allow_html=True)
    st.markdown('<div class="eyebrow" style="margin-top:22px">Jarvis says</div>',
                unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(res["reply"])

pend = store.pending()
if pend:
    st.markdown('<div class="eyebrow">⏳ Awaiting your approval</div>',
                unsafe_allow_html=True)
    st.caption(
        "Nothing has been sent or scheduled. Approve to do it; reject to discard.")
    for p in pend:
        with st.container(border=True):
            if p["kind"] == "email":
                st.markdown(f"✉️ **Email to {p['to']}** — {p['subject']}")
                st.text(p["body"])
            else:
                st.markdown(
                    f"📅 **Event** — {p['title']} on {p['day']} {p['time']}")
            c1, c2, _ = st.columns([1, 1, 3])
            if c1.button("✅ Approve", key=f"a_{p['id']}"):
                store.approve(p["id"])
                st.rerun()
            if c2.button("🗑 Reject", key=f"r_{p['id']}"):
                store.reject(p["id"])
                st.rerun()

# ---- portfolio sections --------------------------------------------------------
st.markdown(
    '<div id="how" class="sec"><div class="eyebrow">How it works</div><h2>Read freely. Stage everything risky.</h2>'
    '<p class="sub">A LangGraph agent on Groq discovers its tools from a real FastMCP server over stdio. '
    'Reads return data, writes only stage a draft, and a human approves.</p></div>'
    '<div class="grid">'
    + card("👁", "1 · Read", "<code>list_inbox</code>, <code>read_email</code>, <code>get_calendar</code> and <code>search_notes</code> return data directly.")
    + card("🧠", "2 · Reason",
           "The agent decides which tools to call and drafts the response.")
    + card("✋", "3 · Stage",
           "<code>draft_reply</code> and <code>propose_event</code> only add items to a pending queue.")
    + card("✅", "4 · Approve",
           "You approve or reject. Only then does anything reach the outbox or calendar.")
    + '</div>', unsafe_allow_html=True)

st.markdown(
    '<div id="safety" class="sec"><div class="eyebrow">Guardrails</div><h2>The prompt isn’t the safety boundary. The code is.</h2>'
    '<p class="sub">Jarvis has no send, schedule, delete or payment tool, so it cannot act unattended. '
    'This public demo adds more layers on top.</p></div><div class="grid">'
    + card("🧱", "No dangerous tools",
           "There is no send or schedule tool to talk the model into using.")
    + card("🏷", "Untrusted data labelling",
           "Email and note content is wrapped and marked as data, never instructions.")
    + card("🔍", "Input screening",
           f"Instructions over {guardrails.MAX_CHARS} characters, override attempts and mail-to-outsider requests are blocked before the model sees them.")
    + card("⏱", "Usage limits",
           f"A {guardrails.COOLDOWN_S}s cooldown, {guardrails.SESSION_CAP} runs per session and a daily cap protect the API key.")
    + card("📝", "Honest output check",
           "If a reply claims something was sent, it is corrected with a note.")
    + card("🎣", "Phishing test built in",
           "The sandbox contains a malicious email. Try the “Phishing test” button above.")
    + '</div>', unsafe_allow_html=True)

st.markdown(
    '<div id="services" class="sec"><div class="eyebrow">Freelance services</div><h2>What I can build for you</h2>'
    '<p class="sub">I’m Sahinul Haque, an AI &amp; Agentic AI developer and technical architect with 21 years of IT experience.</p></div>'
    '<div class="grid">'
    + card("🤖", "Agentic AI systems",
           "Tool-using agents with LangChain and LangGraph, built for real workflows.")
    + card("🔌", "MCP servers &amp; integrations",
           "Custom MCP servers that connect agents to your inbox, calendar, data and tools.")
    + card("🛡", "Human-in-the-loop safety",
           "Approval flows, least-privilege tools and prompt-injection resistance.")
    + card("⚙️", "Automation",
           "Turn repetitive tasks into reliable, supervised AI workflows.")
    + card("🖥", "AI apps &amp; demos",
           "Streamlit interfaces and proofs of concept you can show stakeholders.")
    + card("🏛", "Technical architecture",
           "Design and review of AI solutions, backed by 21 years in IT.")
    + '</div>', unsafe_allow_html=True)

chips = ["FastMCP", "MCP (stdio)", "LangGraph", "LangChain", "Groq",
         "openai/gpt-oss-120b", "Pydantic", "Streamlit", "Python 3.12"]
st.markdown('<div class="sec"><div class="eyebrow">Under the hood</div><h2>Tech used in Jarvis</h2></div><div class="chips">'
            + "".join(f'<span class="chip">{c}</span>' for c in chips) + '</div>', unsafe_allow_html=True)

st.markdown(
    '<div id="hire" class="band"><h2>Have an AI agent project in mind?</h2>'
    '<p class="sub">Let’s talk about what you want to build. Reach out through GitHub, or read the code first.</p>'
    f'<a class="btn p" href="{GITHUB}" target="_blank">Contact via GitHub ↗</a>'
    f'<a class="btn" href="{REPO}" target="_blank">Jarvis repository</a></div>'
    '<div class="foot">© 2026 Sahinul Haque · AI &amp; Agentic AI Developer, Technical Architect · '
    'The demo uses a real model on a sandboxed account: it can’t send real email.</div>',
    unsafe_allow_html=True)

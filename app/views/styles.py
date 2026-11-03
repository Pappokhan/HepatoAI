import streamlit as st

CSS = """
<style>
:root{--primary:#0f766e;--primary-d:#115e59;--primary-l:#ccfbf1;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;
--bg:#f8fafc;--card:#ffffff;--r:14px;
--ok:#15803d;--ok-bg:#dcfce7;--warn:#b45309;--warn-bg:#fef3c7;--bad:#b91c1c;--bad-bg:#fee2e2;}

/* ---- chrome ---- */
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stAppDeployButton"], .stDeployButton{display:none !important;}
html,body{overflow-x:hidden;}
.stApp{background:var(--bg);}
header[data-testid="stHeader"]{background:transparent;height:2.2rem;}
.block-container{padding:2.6rem 2rem 1rem 2rem;max-width:1560px;}
h1,h2,h3,h4,h5{letter-spacing:-0.01em;}
div[data-testid="stVerticalBlock"]{gap:.6rem;}
/* Streamlit's markdown wrapper pulls the next element up (negative bottom margin) -- cancel it and
   give every custom HTML block its own bottom space so blocks can never overlap. */
div[data-testid="stMarkdown"], div[data-testid="stMarkdownContainer"], .stMarkdown{margin-bottom:0 !important;}
div[data-testid="stMarkdownContainer"] > div:last-child{margin-bottom:.45rem;}

/* ---- brand colour even when .streamlit/config.toml is not picked up ---- */
button[kind^="primary"], [data-testid^="stBaseButton-primary"]{
  background:var(--primary) !important;border-color:var(--primary) !important;color:#fff !important;}
button[kind^="primary"]:hover, [data-testid^="stBaseButton-primary"]:hover{
  background:var(--primary-d) !important;border-color:var(--primary-d) !important;}
button[kind^="primary"]:focus-visible, [data-testid^="stBaseButton-primary"]:focus-visible{
  box-shadow:0 0 0 3px rgba(15,118,110,.3) !important;}
div[data-baseweb="input"]:focus-within, div[data-baseweb="base-input"]:focus-within{border-color:var(--primary) !important;}
[data-baseweb="tab-highlight"]{background-color:var(--primary) !important;}
.stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid var(--line);}
.stTabs [data-baseweb="tab"]{height:40px;padding:0 16px;font-weight:600;}
.stTabs [aria-selected="true"], .stTabs [aria-selected="true"] p{color:var(--primary) !important;}
.stTabs [data-baseweb="tab-panel"]{padding-top:.9rem;}

/* ---- header ---- */
.hero{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;
background:linear-gradient(120deg,#0f766e 0%,#0e7490 60%,#155e75 100%);color:#fff;
border-radius:var(--r);padding:14px 24px;margin-bottom:.6rem;box-shadow:0 6px 18px rgba(15,118,110,.18);}
.hero-l{display:flex;align-items:center;gap:14px;}
.hero-ico{position:relative;flex:none;width:42px;height:42px;border-radius:12px;background:rgba(255,255,255,.18);
border:1px solid rgba(255,255,255,.3);}
.hero-ico i{position:absolute;left:50%;top:50%;width:20px;height:6px;margin:-3px 0 0 -10px;border-radius:2px;background:#fff;}
.hero-ico i::after{content:"";position:absolute;left:7px;top:-7px;width:6px;height:20px;border-radius:2px;background:#fff;}
.hero h1{color:#fff;font-size:1.45rem;margin:0;padding:0;line-height:1.15;}
.hero p{color:#ccfbf1;margin:2px 0 0 0;font-size:.85rem;}
.hero-r{display:flex;gap:8px;flex-wrap:wrap;}
.chip{display:inline-flex;align-items:center;height:26px;background:rgba(255,255,255,.16);
border:1px solid rgba(255,255,255,.28);color:#fff;border-radius:999px;padding:0 12px;font-size:.76rem;white-space:nowrap;}

/* ---- input card ---- */
div[data-testid="stForm"]{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:20px 22px 22px;}
div[data-testid="stForm"] div[data-testid="stVerticalBlock"]{gap:.5rem;}
div[data-testid="stForm"] div[data-testid="stHorizontalBlock"]{gap:1rem;align-items:flex-start;}
.form-title{font-size:1.05rem;font-weight:700;color:var(--ink);line-height:1.3;margin:0 0 .45rem 0;}
.form-title.mt{margin-top:.7rem;}
.opt{font-weight:500;font-size:.72rem;color:var(--muted);background:var(--line);border-radius:999px;padding:1px 9px;margin-left:8px;vertical-align:middle;}
.group-title{font-weight:700;color:var(--primary);font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;
border-bottom:2px solid var(--primary-l);padding-bottom:5px;margin:.5rem 0 .55rem 0;}
div[data-testid="stWidgetLabel"]{margin-bottom:2px;min-height:1.4rem;}
div[data-testid="stWidgetLabel"] p{font-size:.8rem;font-weight:600;color:#334155;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
div[data-testid="stNumberInput"] input, div[data-testid="stTextInput"] input{height:2.5rem;padding-top:.3rem;padding-bottom:.3rem;}
div[data-testid="stNumberInput"] div[data-baseweb="input"], div[data-testid="stTextInput"] div[data-baseweb="input"]{min-height:2.5rem;}
div[data-testid="stNumberInput"] button{height:2.5rem;}

/* ---- buttons ---- */
div[data-testid="stFormSubmitButton"] button, div[data-testid="stDownloadButton"] button, div.stButton button{
border-radius:10px;font-weight:600;min-height:2.6rem;padding:.4rem 1rem;}
div[data-testid="stFormSubmitButton"] button, div[data-testid="stDownloadButton"] button, div.stButton button{width:100%;white-space:normal;}

/* ---- model note ---- */
.model-note{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:16px 22px;font-size:.84rem;color:#334155;}
.mn-title{font-weight:700;color:var(--ink);font-size:.95rem;margin-bottom:8px;}
.mn-grid{display:grid;grid-template-columns:max-content 1fr;gap:5px 18px;margin-bottom:10px;}
.mn-grid span{color:var(--muted);} .mn-grid b{color:var(--ink);font-weight:600;}
.model-note p{margin:0 !important;color:var(--muted);line-height:1.45;}

/* ---- result card ---- */
.result-card{position:relative;display:flex;justify-content:space-between;align-items:center;gap:16px;overflow:hidden;
border-radius:var(--r);padding:16px 22px 16px 28px;border:1px solid var(--line);background:var(--card);}
.result-card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:6px;background:var(--muted);}
.result-card.ok{background:var(--ok-bg);border-color:#86efac;} .result-card.ok::before{background:var(--ok);}
.result-card.bad{background:var(--bad-bg);border-color:#fca5a5;} .result-card.bad::before{background:var(--bad);}
.rc-kicker{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:700;}
.rc-title{font-size:1.25rem;font-weight:800;color:var(--ink);margin:3px 0 6px;line-height:1.2;}
.rc-sub{color:#334155;font-size:.9rem;display:flex;align-items:center;gap:8px;}
.rc-side{text-align:right;flex:none;}
.rc-prob{font-size:2.1rem;font-weight:800;line-height:1;}
.result-card.ok .rc-prob{color:var(--ok);} .result-card.bad .rc-prob{color:var(--bad);}
.rc-probl{font-size:.78rem;color:#475569;margin-top:4px;}
.pill{display:inline-block;border-radius:999px;padding:1px 10px;font-weight:700;font-size:.8rem;}
.pill.ok{background:#bbf7d0;color:var(--ok);} .pill.warn{background:#fde68a;color:var(--warn);} .pill.bad{background:#fecaca;color:var(--bad);}
.meter{position:relative;height:10px;border-radius:6px;background:var(--line);margin:10px 0 4px;overflow:hidden;}
.meter-fill{height:100%;border-radius:6px;}
.meter-fill.ok{background:var(--ok);} .meter-fill.bad{background:var(--bad);}
.meter-mid{position:absolute;left:50%;top:0;bottom:0;width:2px;margin-left:-1px;background:#475569;opacity:.55;}
.meter-scale{display:grid;grid-template-columns:1fr auto 1fr;font-size:.72rem;color:var(--muted);}
.meter-scale span:first-child{text-align:left;} .meter-scale span:nth-child(2){text-align:center;} .meter-scale span:last-child{text-align:right;}

.notice{background:var(--warn-bg);border:1px solid #fcd34d;border-radius:12px;padding:10px 16px;font-size:.86rem;color:#78350f;}
.notice b{color:var(--warn);} .notice p{margin:3px 0 0 0 !important;line-height:1.45;}

.section-title{font-size:1.05rem;font-weight:700;color:var(--ink);margin:.6rem 0 0;line-height:1.3;}

/* ---- biomarker table ---- */
.mk-wrap{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;overflow-x:auto;}
.mk-wrap .mk-table{width:100%;min-width:560px;table-layout:fixed;border-collapse:collapse;border:0;margin:0;font-size:.84rem;}
.mk-wrap .mk-table th, .mk-wrap .mk-table td{border:0;border-top:1px solid var(--line);padding:7px 12px;text-align:left;vertical-align:middle;background:transparent;}
.mk-wrap .mk-table th{border-top:0;background:#f1f5f9;color:#334155;font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;padding:8px 12px;white-space:nowrap;}
.mk-wrap .mk-table tr.row-bad td{background:#fef2f2;} .mk-wrap .mk-table tr.row-warn td{background:#fffbeb;}
.mk-name{font-weight:600;} .mk-val{white-space:nowrap;font-variant-numeric:tabular-nums;} .mk-rng{white-space:nowrap;font-variant-numeric:tabular-nums;color:#334155;}
.unit{color:var(--muted);font-size:.78rem;}
.track{position:relative;height:8px;background:var(--line);border-radius:4px;margin:3px 7px 3px 7px;}
.zone{position:absolute;top:0;bottom:0;background:#5eead4;border-radius:4px;min-width:4px;}
.dot{position:absolute;top:50%;width:14px;height:14px;border-radius:50%;transform:translate(-50%,-50%);box-sizing:border-box;
border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.35);background:var(--muted);}
.dot.ok{background:var(--ok);} .dot.warn{background:var(--warn);} .dot.bad{background:var(--bad);}
.badge{display:inline-block;min-width:62px;text-align:center;border-radius:6px;padding:2px 10px;font-size:.76rem;font-weight:700;}
.badge.ok{background:var(--ok-bg);color:var(--ok);} .badge.warn{background:var(--warn-bg);color:var(--warn);}
.badge.bad{background:var(--bad-bg);color:var(--bad);} .badge.muted{background:var(--line);color:var(--muted);}
.table-note{font-size:.8rem;color:var(--muted);}

.callout{background:#f0fdfa;border:1px solid #99f6e4;border-radius:12px;padding:12px 18px;font-size:.88rem;}
.callout ul{margin:6px 0 0 18px;padding:0;} .callout li{margin-bottom:3px;}
div[data-testid="stExpander"] details{border:1px solid var(--line);border-radius:12px;background:var(--card);}
div[data-testid="stExpander"] details summary{padding:.55rem .9rem;}
.empty{border:2px dashed #cbd5e1;border-radius:var(--r);padding:48px 24px;text-align:center;color:var(--muted);background:var(--card);}
.app-footer{text-align:center;color:var(--muted);font-size:.78rem;margin-top:.6rem;padding-top:.6rem;border-top:1px solid var(--line);}
div[data-testid="stAlert"]{padding:.55rem .85rem;border-radius:12px;}
div[data-testid="stChatInput"]{padding-bottom:.2rem;}
div[data-testid="stMetric"]{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;}

/* ---- AI assistant: ChatGPT-style ---- */
.ctx{display:flex;align-items:center;gap:8px;font-size:.84rem;color:var(--muted);}
.ctx span{width:8px;height:8px;border-radius:50%;background:#cbd5e1;flex:none;}
.ctx.ok{color:#166534;} .ctx.ok span{background:var(--ok);box-shadow:0 0 0 3px var(--ok-bg);}
[class*="st-key-test_ai"] button, [class*="st-key-clear_chat"] button{background:transparent;border:1px solid var(--line);
color:#334155;min-height:2.2rem;font-size:.82rem;}
[class*="st-key-test_ai"] button:hover, [class*="st-key-clear_chat"] button:hover{background:#f1f5f9;border-color:#cbd5e1;color:var(--ink);}

.chat-welcome{text-align:center;padding:56px 0 22px;}
.cw-badge{position:relative;width:48px;height:48px;border-radius:50%;background:var(--primary);margin:0 auto 14px;}
.cw-badge i{position:absolute;left:50%;top:50%;width:22px;height:6px;margin:-3px 0 0 -11px;border-radius:2px;background:#fff;}
.cw-badge i::after{content:"";position:absolute;left:8px;top:-8px;width:6px;height:22px;border-radius:2px;background:#fff;}
.chat-welcome h3{margin:0 0 6px;padding:0;font-size:1.5rem;font-weight:700;color:var(--ink);}
.chat-welcome p{color:var(--muted);font-size:.95rem;}
[class*="st-key-qp_"] button{min-height:4.2rem;border-radius:16px;background:var(--card);border:1px solid var(--line);
color:#334155;font-weight:500;font-size:.88rem;text-align:left;justify-content:flex-start;padding:.7rem 1rem;line-height:1.35;}
[class*="st-key-qp_"] button:hover{background:#f1f5f9;border-color:#cbd5e1;color:var(--ink);}

div[data-testid="stChatMessage"]{background:transparent !important;padding:.55rem .2rem;gap:.85rem;align-items:flex-start;}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"], [data-testid="chatAvatarIcon-user"]){flex-direction:row-reverse;}
[data-testid="stChatMessageAvatarUser"], [data-testid="chatAvatarIcon-user"]{display:none !important;}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"], [data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"]{
  flex:0 1 auto;max-width:78%;background:#eceff4;border-radius:20px;padding:.65rem 1.05rem;}
[data-testid="stChatMessageAvatarAssistant"], [data-testid="chatAvatarIcon-assistant"]{background:var(--primary) !important;color:#fff !important;}
[data-testid="stChatMessageContent"]{font-size:.96rem;line-height:1.65;}
[data-testid="stChatMessageContent"] p{margin:0 0 .6rem;} [data-testid="stChatMessageContent"] p:last-child{margin-bottom:0;}

div[data-testid="stChatInput"]{padding:.4rem 0 .2rem;}
div[data-testid="stChatInput"] > div{background:var(--card) !important;border:1px solid #cbd5e1;border-radius:28px;
box-shadow:0 2px 10px rgba(15,23,42,.06);}
div[data-testid="stChatInput"] > div:focus-within{border-color:var(--primary);box-shadow:0 0 0 3px rgba(15,118,110,.15);}
div[data-testid="stChatInput"] textarea{background:transparent !important;font-size:.96rem;padding-left:1.1rem;}
button[data-testid="stChatInputSubmitButton"]{background:var(--primary) !important;border-radius:50% !important;color:#fff !important;}
button[data-testid="stChatInputSubmitButton"]:disabled{background:#cbd5e1 !important;}
button[data-testid="stChatInputSubmitButton"] svg{fill:#fff;color:#fff;}

@media (max-width:900px){
  .block-container{padding:2.4rem 1rem 1rem 1rem;}
  .hero{padding:12px 16px;} .hero-r{display:none;}
  .rc-prob{font-size:1.7rem;}
  .result-card{flex-wrap:wrap;} .rc-side{text-align:left;}
}
@media (max-height:820px){
  .hero p{display:none;}
}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def html(s: str) -> str:
    """Strip indentation and blank lines so Markdown never turns HTML into a code block or cuts it short."""
    return "\n".join(line.strip() for line in s.splitlines() if line.strip())

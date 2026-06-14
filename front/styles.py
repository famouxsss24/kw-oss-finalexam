import streamlit as st


CSS = """
<style>
.stApp { background:#080a0d; color:#eef2f6; }
[data-testid="stSidebar"] { background:#0b0e13; border-right:1px solid #2a3240; }
#MainMenu, footer { visibility:hidden; }

.block-container { max-width:900px !important; margin:0 auto !important;
                   padding-top:2.5rem !important; padding-bottom:3rem !important; }
.stMainBlockContainer { max-width:900px !important; margin:0 auto !important;
                        padding-top:2.5rem !important; padding-bottom:3rem !important; }
[data-testid="stMainBlockContainer"] { max-width:900px !important; margin:0 auto !important; }
section.main .block-container { max-width:900px !important; margin:0 auto !important; }

[data-testid="stPills"] button { border-radius:20px !important; }
.stButton button p, .stButton button { word-break:keep-all; white-space:nowrap; }

.df-branch-card { background:#0e1626; border:1px solid #1e2b48; border-radius:16px;
                  padding:24px 22px 8px; height:100%; }
.df-branch-card.alert { border-top:3px solid #f87171; }
.df-branch-card.guard { border-top:3px solid #22d3ee; }
.df-branch-card h3 { font-size:18px; margin:0 0 12px; line-height:1.45; word-break:keep-all; }
.df-branch-card p { color:#8499c0; font-size:13px; line-height:1.6; min-height:44px; margin:0; word-break:keep-all; }
.df-ask { text-align:center; font-size:22px; font-weight:700; margin:8px 0 22px; word-break:keep-all; }

.df-brand { text-align:center; padding:24px 0 6px; }
.df-brand .ko { font-size:42px; font-weight:900; letter-spacing:-1px;
                background:linear-gradient(90deg,#fff,#9fd8ff);
                -webkit-background-clip:text; background-clip:text; color:transparent; }
.df-brand .en { font-size:12px; letter-spacing:6px; color:#22d3ee; font-weight:700; margin-top:4px; }
.df-brand .sub { font-size:14px; color:#8499c0; margin-top:12px; }

.df-bar { display:flex; gap:8px; margin:8px 0 6px; }
.df-bar > div { flex:1; height:6px; border-radius:6px; background:#16223c; }
.df-bar > div.on { background:linear-gradient(90deg,#22d3ee,#3b82f6); }
.df-step { font-size:12px; color:#8499c0; letter-spacing:1px; margin-bottom:2px; }

.df-q { font-size:26px; font-weight:800; margin:6px 0 2px; word-break:keep-all; }
.df-help { font-size:14px; color:#8499c0; margin-bottom:18px; word-break:keep-all; }

div[role="radiogroup"] { gap:10px; }
div[role="radiogroup"] > label { background:#0e1626; border:1px solid #1e2b48; border-radius:12px;
                                 padding:14px 16px; margin:0; transition:.15s; }
div[role="radiogroup"] > label:hover { border-color:#22d3ee; }

.gauge-wrap { background:#111a30; border:1px solid #1e2b48; border-radius:14px; padding:22px 24px; margin:6px 0 14px; }
.gauge-top { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:12px; }
.gauge-score { font-size:40px; font-weight:900; }
.gauge-score small { font-size:15px; color:#8499c0; font-weight:600; }
.gauge-lvl { font-size:14px; font-weight:800; letter-spacing:1px; }
.gauge-bar { height:12px; background:#16223c; border-radius:8px; overflow:hidden; }
.gauge-bar > i { display:block; height:100%; border-radius:8px; }
.gauge-meta { display:flex; flex-wrap:wrap; gap:22px; margin-top:14px; font-size:13px; color:#8499c0; }
.gauge-meta b { color:#eef2f6; }

.rec { background:#0e1626; border:1px solid #1e2b48; border-left:3px solid #22d3ee;
       border-radius:10px; padding:14px 16px; margin-bottom:10px; }
.rec .badge { font-size:11px; font-weight:700; padding:3px 9px; border-radius:6px;
              background:rgba(34,211,238,.12); color:#22d3ee; margin-left:8px; }
.rec .rt { font-weight:700; }
.rec .rd { color:#8499c0; font-size:13px; margin-top:5px; }
.reg-box { margin-top:10px; padding:14px 16px; border:1px dashed #1e2b48; border-radius:10px;
           font-size:13px; color:#8499c0; }
.reg-box b { color:#f59e0b; }
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

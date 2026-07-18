"""PIN opcional SIGCF — logo Santa Virgínia e tema visual padrão SIGCF."""
import base64
from pathlib import Path

import streamlit as st

LOGO_URL = "https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg"
LOGO_FILE = Path(__file__).resolve().parent / "assets" / "logo_santa_verginia.png"
BG_URL = "https://media.bio.site/sites/32a25c2c-d6fa-4dfc-bdc2-27e4d35d7ea2/AhS9mKiQxFRXAyMBdXDzEG.jpg"
SESSION_KEY = "sigcf_auth"

LOGO_FRAME_CSS = """
.logo-frame{background:linear-gradient(145deg,#0a1628,#0d2040);border:2px solid #c9a227;
 border-radius:12px;padding:5px;display:inline-block;box-shadow:0 4px 18px rgba(0,0,0,.45);}
.logo-frame img{display:block;border-radius:8px;}
"""


def logo_html(width: int = 118) -> str:
    if LOGO_FILE.is_file():
        b64 = base64.b64encode(LOGO_FILE.read_bytes()).decode()
        src = f"data:image/png;base64,{b64}"
    else:
        src = LOGO_URL
    return f'<div class="logo-frame"><img src="{src}" width="{width}" alt="Santa Virgínia"></div>'


def aplicar_tema_sigcf(*, sidebar: bool = False):
    """Fundo fazenda + overlay verde, tipografia e KPIs no padrão SIGCF."""
    sidebar_css = ""
    if sidebar:
        sidebar_css = """
[data-testid="stSidebar"]{background:rgba(13,24,12,0.92)!important;
 backdrop-filter:blur(8px);border-right:1px solid #1e2e1c;}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] span{color:#e8edd0;}
[data-testid="stSidebar"] .stCaption{color:#8aab80!important;}
"""
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&display=swap');
.stApp{{
 background:linear-gradient(rgba(10,20,9,0.84),rgba(10,20,9,0.93)),
 url('{BG_URL}') center center/cover no-repeat fixed!important;
}}
[data-testid="stAppViewContainer"]{{background:transparent!important;}}
[data-testid="stHeader"]{{background:transparent!important;}}
{sidebar_css}
h1,h2,h3,h4,p,span,label{{color:#e8edd0;}}
h1,h2,h3{{font-family:'Barlow Condensed',sans-serif;letter-spacing:0.5px;}}
.stCaption,[data-testid="stCaptionContainer"] p{{color:#8aab80!important;}}
.sec{{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;
 letter-spacing:2px;text-transform:uppercase;color:#8aab80;
 border-left:4px solid #4a9e3f;padding-left:10px;margin:18px 0 12px;}}
{LOGO_FRAME_CSS.strip()}
div[data-testid="stMetric"],div[data-testid="metric-container"]{{
 background:rgba(13,24,12,0.88)!important;border:1px solid #1e2e1c!important;
 border-radius:10px;padding:12px 16px!important;backdrop-filter:blur(4px);}}
div[data-testid="stMetric"] label,div[data-testid="metric-container"] label{{
 color:#8aab80!important;font-size:11px!important;text-transform:uppercase;
 letter-spacing:1px;font-family:'Barlow Condensed',sans-serif;}}
div[data-testid="stMetricValue"],div[data-testid="metric-container"] [data-testid="stMetricValue"]{{
 color:#6fcf60!important;font-family:'Barlow Condensed',sans-serif;font-size:1.6rem!important;}}
.kpi-destaque{{background:rgba(13,24,12,0.92)!important;border:1px solid #4a9e3f!important;
 border-radius:10px;padding:14px 18px;margin-top:8px;}}
.filtros-bar{{background:rgba(13,24,12,0.88);border:1px solid #1e2e1c;border-radius:10px;
 padding:12px 16px;margin-bottom:16px;backdrop-filter:blur(4px);}}
.stTabs [data-baseweb="tab-list"]{{background:rgba(13,24,12,0.75);border-bottom:1px solid #1e2e1c;gap:4px;}}
.stTabs [data-baseweb="tab"]{{color:#8aab80!important;font-family:'Barlow Condensed',sans-serif;
 font-weight:600;letter-spacing:0.5px;}}
.stTabs [aria-selected="true"]{{color:#e8edd0!important;border-bottom-color:#4a9e3f!important;}}
.stTabs [data-baseweb="tab-highlight"]{{background-color:#4a9e3f!important;}}
.stTextInput input,.stNumberInput input,.stTextArea textarea,
[data-testid="stDateInput"] input,[data-testid="stTimeInput"] input{{
 background:#dce6d2!important;color:#1a2818!important;border:1px solid #4a6644!important;border-radius:8px!important;}}
div[data-baseweb="select"] > div{{
 background:#dce6d2!important;border:1px solid #4a6644!important;color:#1a2818!important;border-radius:8px!important;}}
div[data-baseweb="select"] div{{color:#1a2818!important;}}
[data-testid="stForm"]{{
 background:rgba(13,24,12,0.92)!important;border:1px solid #1e2e1c!important;border-radius:12px;padding:16px;}}
[data-testid="stExpander"]{{
 background:rgba(13,24,12,0.88)!important;border:1px solid #1e2e1c!important;border-radius:10px;}}
[data-testid="stExpander"] summary{{color:#e8edd0!important;}}
.stButton button,[data-testid="stFormSubmitButton"] button,[data-testid="stDownloadButton"] button{{
 background:#4a9e3f!important;color:#fff!important;border:1px solid #6fcf60!important;
 font-family:'Barlow Condensed',sans-serif;font-weight:700;letter-spacing:1px;border-radius:8px;}}
.stButton button:hover,[data-testid="stFormSubmitButton"] button:hover{{background:#3d8534!important;}}
</style>
""",
        unsafe_allow_html=True,
    )


def dark_table(df, height: int = 260):
    import pandas as pd

    if df.empty:
        st.info("Nenhum registro.")
        return
    rows = "".join(
        "<tr>"
        + "".join(
            f'<td style="padding:6px 10px;border-bottom:1px solid #1e2e1c;'
            f'color:#e8edd0;font-size:12px;white-space:nowrap;">{v}</td>'
            for v in row
        )
        + "</tr>"
        for _, row in df.iterrows()
    )
    headers = "".join(
        f'<th style="padding:7px 10px;background:rgba(17,28,16,0.95);color:#8aab80;font-size:10px;'
        f'font-weight:700;text-transform:uppercase;letter-spacing:1px;'
        f'border-bottom:2px solid #1e2e1c;white-space:nowrap;">{c}</th>'
        for c in df.columns
    )
    st.markdown(
        f'<div style="overflow-x:auto;border:1px solid #1e2e1c;border-radius:10px;">'
        f'<div style="max-height:{height}px;overflow-y:auto;">'
        f'<table style="width:100%;border-collapse:collapse;background:rgba(13,24,12,0.92);'
        f'font-family:Barlow Condensed,sans-serif;"><thead><tr>{headers}</tr></thead>'
        f'<tbody>{rows}</tbody></table></div></div>',
        unsafe_allow_html=True,
    )


def exigir_acesso(titulo: str, subtitulo: str = "Acesso restrito — SIGCF Santa Virgínia"):
    pin_cfg = str(st.secrets.get("APP_PIN", "") or "").strip()
    if not pin_cfg:
        return
    if st.session_state.get(SESSION_KEY):
        return

    aplicar_tema_sigcf()
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.markdown(logo_html(), unsafe_allow_html=True)
    with col_titulo:
        st.title(titulo)
        st.caption(subtitulo)

    pin = st.text_input("PIN de acesso", type="password", key="sigcf_login_pin")
    if st.button("Entrar", type="primary", key="sigcf_login_btn"):
        if pin == pin_cfg:
            st.session_state[SESSION_KEY] = True
            st.rerun()
        else:
            st.error("PIN incorreto.")
    st.stop()

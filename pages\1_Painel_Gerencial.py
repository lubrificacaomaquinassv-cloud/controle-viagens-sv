# -*- coding: utf-8 -*-
"""SIG Frota — Painel Gerencial (página separada no Streamlit)."""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from io import BytesIO
from supabase import create_client

from sigcf_auth import exigir_acesso, logo_html

BUILD = "2026-07-18-painel-v2"

exigir_acesso("SIG Frota — Painel Gerencial", "Gestão · viagens, destinos e fechamento — SIGCF SV")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&display=swap');
[data-testid="stAppViewContainer"]{background:#0a1409;}
[data-testid="stSidebar"]{background:#111c10;border-right:1px solid #1e2e1c;}
h1,h2,h3,p,span,label{color:#e8edd0;}
.stCaption{color:#8aab80!important;}
.sec{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;
 letter-spacing:2px;text-transform:uppercase;color:#8aab80;
 border-left:4px solid #4a9e3f;padding-left:10px;margin:16px 0 10px;}
div[data-testid="metric-container"]{background:#111c10;border:1px solid #1e2e1c;border-radius:10px;padding:14px;}
div[data-testid="metric-container"] label{color:#8aab80!important;}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{color:#6fcf60!important;
 font-family:'Barlow Condensed',sans-serif;}
.stTabs [data-baseweb="tab-list"]{background:#111c10;border-bottom:2px solid #1e2e1c;}
.stTabs [aria-selected="true"]{color:#6fcf60!important;border-bottom:3px solid #4a9e3f!important;}
.fechamento-box{background:#111c10;border:1px solid #4a9e3f;border-radius:12px;padding:18px;margin:8px 0;}
</style>
""", unsafe_allow_html=True)

PDARK = dict(
    paper_bgcolor="#111c10", plot_bgcolor="#0d180c",
    font=dict(color="#e8edd0", family="Barlow Condensed"),
    margin=dict(l=10, r=10, t=36, b=10),
)

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def fmt_r(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "R$ 0,00"


def fmt_km(v):
    try:
        return f"{float(v):,.0f} km".replace(",", ".")
    except (TypeError, ValueError):
        return "0 km"


@st.cache_data(ttl=60)
def carregar_viagens(data_ini: str, data_fim: str):
    try:
        res = (
            supabase.table("vw_sig_frota_painel")
            .select("*")
            .gte("data_hora", data_ini)
            .lte("data_hora", data_fim + "T23:59:59")
            .order("data_hora", desc=True)
            .execute()
        )
        return pd.DataFrame(res.data or [])
    except Exception:
        res = (
            supabase.table("viagem_veiculo")
            .select("*")
            .gte("data_hora", data_ini)
            .lte("data_hora", data_fim + "T23:59:59")
            .order("data_hora", desc=True)
            .execute()
        )
        df = pd.DataFrame(res.data or [])
        if not df.empty and "id_frota" in df.columns and "placa" not in df.columns:
            df["placa"] = df["id_frota"]
        return df


def gerar_excel(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


with st.sidebar:
    st.markdown(logo_html(90), unsafe_allow_html=True)
    st.markdown("### 📊 Painel Gerencial")
    st.caption(f"Build {BUILD}")
    st.divider()
    st.markdown("**Período de viagens**")
    hoje = date.today()
    preset = st.selectbox("Atalho", [
        "Este mês", "Mês anterior", "Últimos 30 dias", "Últimos 7 dias", "Personalizado",
    ])
    if preset == "Este mês":
        d_ini, d_fim = hoje.replace(day=1), hoje
    elif preset == "Mês anterior":
        primeiro = hoje.replace(day=1)
        d_fim = primeiro - timedelta(days=1)
        d_ini = d_fim.replace(day=1)
    elif preset == "Últimos 30 dias":
        d_ini, d_fim = hoje - timedelta(days=30), hoje
    elif preset == "Últimos 7 dias":
        d_ini, d_fim = hoje - timedelta(days=7), hoje
    else:
        d_ini = st.date_input("De", value=hoje.replace(day=1))
        d_fim = st.date_input("Até", value=hoje)
    filtro_linha = st.multiselect("Linha", ["LEVE", "PESADA"], default=["LEVE", "PESADA"])
    filtro_tipo = st.multiselect("Tipo", ["INTERNA", "EXTERNA"], default=["INTERNA", "EXTERNA"])
    st.caption("Dados atualizados automaticamente")

df = carregar_viagens(str(d_ini), str(d_fim))
if not df.empty:
    df["data_hora"] = pd.to_datetime(df["data_hora"], errors="coerce")
    if "locais_internos" not in df.columns and "retiros" in df.columns:
        df["locais_internos"] = df["retiros"]
    if "placa" not in df.columns and "id_frota" in df.columns:
        df["placa"] = df["id_frota"]
    if "linha" in df.columns:
        df = df[df["linha"].isin(filtro_linha)]
    if "tipo_viagem" in df.columns:
        df = df[df["tipo_viagem"].isin(filtro_tipo)]

st.markdown("## 🚘 SIG Frota — Painel Gerencial")
st.caption(f"Período: {d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}")

if df.empty:
    st.info("Nenhuma viagem no período. Lançamentos aparecem aqui automaticamente.")
    st.stop()

km_total = float(df["km_percorrido"].sum())
m1, m2, m3, m4 = st.columns(4)
m1.metric("Viagens", len(df))
m2.metric("KM percorridos", fmt_km(km_total))
m3.metric("Veículos", df["placa"].nunique())
m4.metric("Internas / Externas", f"{len(df[df['tipo_viagem']=='INTERNA'])} / {len(df[df['tipo_viagem']=='EXTERNA'])}")

st.markdown('<div class="sec">💰 Fechamento do período</div>', unsafe_allow_html=True)
litros = float(df["litros_abastecidos"].sum()) if "litros_abastecidos" in df.columns else 0
v_abast = float(df["valor_abastecimento"].sum()) if "valor_abastecimento" in df.columns else 0
v_ped = float(df["valor_pedagio"].sum()) if "valor_pedagio" in df.columns else 0
v_manut = float(df["valor_manutencao"].sum()) if "valor_manutencao" in df.columns else 0
v_mot = float(df["valor_motorista"].sum()) if "valor_motorista" in df.columns else 0
custo_total = v_abast + v_ped + v_manut + v_mot
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Litros", f"{litros:,.1f} L".replace(",", "."))
c2.metric("Abastecimento", fmt_r(v_abast))
c3.metric("Pedágio", fmt_r(v_ped))
c4.metric("Manutenção", fmt_r(v_manut))
c5.metric("Motorista", fmt_r(v_mot))
c6.metric("Custo total", fmt_r(custo_total))

tab1, tab2, tab3 = st.tabs(["🚗 Viagens", "📍 Destinos", "📈 Resumo"])

with tab1:
    show = df.copy()
    show["Data/Hora"] = show["data_hora"].dt.strftime("%d/%m/%Y %H:%M")
    show["Destino"] = show.apply(
        lambda r: ", ".join(r["locais_internos"]) if isinstance(r.get("locais_internos"), list)
        else (r.get("destino_cidade") or "—"), axis=1)
    cols = ["Data/Hora", "placa", "linha", "tipo_viagem", "km_percorrido", "motivo", "Destino"]
    tabela = show[[c for c in cols if c in show.columns]].rename(columns={
        "placa": "Placa", "linha": "Linha", "tipo_viagem": "Tipo",
        "km_percorrido": "KM", "motivo": "Motivo",
    })
    st.dataframe(tabela, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Excel", gerar_excel(tabela), f"viagens_{d_ini}.xlsx")

with tab2:
    df_ext = df[df["tipo_viagem"] == "EXTERNA"]
    if not df_ext.empty:
        dest = df_ext.groupby("destino_cidade").size().reset_index(name="Viagens").sort_values("Viagens", ascending=False)
        st.dataframe(dest, use_container_width=True, hide_index=True)
    locais = []
    for val in df[df["tipo_viagem"] == "INTERNA"].get("locais_internos", pd.Series()).dropna():
        if isinstance(val, list):
            locais.extend(val)
    if locais:
        st.dataframe(pd.Series(locais).value_counts().reset_index(name="Visitas"), use_container_width=True)

with tab3:
    if "placa" in df.columns:
        por_placa = df.groupby("placa")["km_percorrido"].sum().reset_index()
        fig = px.bar(por_placa, x="placa", y="km_percorrido", title="KM por placa")
        fig.update_layout(**PDARK)
        st.plotly_chart(fig, use_container_width=True)

st.caption("SIG Frota | Painel Gerencial | SV")

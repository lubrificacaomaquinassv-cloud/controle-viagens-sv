# -*- coding: utf-8 -*-
"""Controle de Viagens — Veículos Linha Leve e Pesada | SIGCF Santa Vergínia"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta, date
from pathlib import Path
from supabase import create_client

PAINEL_BUILD = "2026-07-18-v1"
LOGO_URL = "https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg"
DIR = Path(__file__).resolve().parent
MAPA_FAZENDA = DIR / "assets" / "mapa_fazenda.png"

# Centro aproximado Bataguassu-MS (ajuste conforme GPS da fazenda)
FAZENDA_CENTER = (-21.7167, -52.4217)

MOTIVOS_PADRAO = [
    "Buscar material",
    "Levar colaborador",
    "Buscar peças / insumos",
    "Serviço em fornecedor",
    "Visita técnica",
    "Entrega / retirada documentos",
    "Emergência / plantão",
    "Outro (descrever abaixo)",
]

CIDADES_COMUNS = [
    "Bataguassu — MS",
    "Bataguassu — Centro",
    "Anastácio — MS",
    "Aquidauana — MS",
    "Campo Grande — MS",
    "Dourados — MS",
    "Nova Andradina — MS",
    "Três Lagoas — MS",
    "Outra (informar abaixo)",
]

CATS_VEICULO = frozenset({"VEICULO_LEVE", "VEICULO_PESADO", "CAMINHAO", "MOTO"})

st.set_page_config(
    page_title="Controle de Viagens — SV",
    layout="wide",
    page_icon="🚗",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&display=swap');
[data-testid="stAppViewContainer"]{background:#0a1409;}
[data-testid="stSidebar"]{background:#111c10;border-right:1px solid #1e2e1c;}
[data-testid="stHeader"]{background:#0a1409;}
h1,h2,h3,h4,p,span,label{color:#e8edd0;}
.stCaption,[data-testid="stCaptionContainer"] p{color:#8aab80!important;}
.stMarkdown p,.stMarkdown li{color:#c8d8c0;}
.stAlert p{color:#e8edd0!important;}
.sec{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;
     letter-spacing:2px;text-transform:uppercase;color:#8aab80;
     border-left:4px solid #4a9e3f;padding-left:10px;margin:18px 0 10px;}
.stTabs [data-baseweb="tab-list"]{background:#111c10;border-bottom:2px solid #1e2e1c;gap:0;}
.stTabs [data-baseweb="tab"]{color:#4a6644;font-family:'Barlow Condensed',sans-serif;
     font-size:12px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
     padding:10px 20px;border-bottom:3px solid transparent;}
.stTabs [aria-selected="true"]{color:#6fcf60!important;border-bottom:3px solid #4a9e3f!important;}
div[data-testid="metric-container"]{background:#111c10;border:1px solid #1e2e1c;border-radius:10px;padding:14px;}
div[data-testid="metric-container"] label{color:#8aab80!important;font-size:11px!important;}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{color:#e8edd0!important;}
div[data-testid="stForm"]{background:#111c10;border:1px solid #1e2e1c;border-radius:12px;padding:20px;}
div[data-testid="stSelectbox"] label,div[data-testid="stNumberInput"] label,
div[data-testid="stDateInput"] label,div[data-testid="stTimeInput"] label,
div[data-testid="stTextArea"] label,div[data-testid="stTextInput"] label,
div[data-testid="stRadio"] label,div[data-testid="stMultiSelect"] label{
 color:#8aab80!important;font-family:'Barlow Condensed',sans-serif;
 text-transform:uppercase;letter-spacing:1px;font-size:11px!important;}
div[data-testid="stRadio"] div[role="radiogroup"] p{color:#e8edd0!important;text-transform:none;}
div[data-baseweb="select"] > div{background:#0d180c!important;border:1px solid #1e2e1c!important;color:#e8edd0!important;}
.stNumberInput input,.stTextInput input,.stTextArea textarea,.stTimeInput input{
 background:#0d180c!important;border:1px solid #1e2e1c!important;color:#e8edd0!important;}
.stButton button,[data-testid="stFormSubmitButton"] button{
 background:#4a9e3f!important;color:#ffffff!important;border:1px solid #6fcf60!important;
 font-family:'Barlow Condensed',sans-serif;font-weight:700;letter-spacing:1px;
 text-transform:uppercase;border-radius:8px;}
.stButton button:hover,[data-testid="stFormSubmitButton"] button:hover{background:#3d8534!important;}
.logo-box{background:#ffffff;border-radius:10px;padding:8px 12px;display:inline-block;}
.badge-leve{background:#1a3a5c;color:#7ec8ff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;}
.badge-pesada{background:#3a2a10;color:#ffc857;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;}
</style>
""", unsafe_allow_html=True)

PDARK = dict(
    paper_bgcolor="#111c10", plot_bgcolor="#0d180c",
    font=dict(color="#e8edd0", family="Barlow Condensed"),
    margin=dict(l=10, r=10, t=40, b=10),
)


def exigir_pin():
    pin_cfg = str(st.secrets.get("APP_PIN", "") or "").strip()
    if not pin_cfg:
        return True
    if st.session_state.get("viagem_auth_ok"):
        return True
    st.markdown("### 🔐 Acesso ao painel")
    pin = st.text_input("PIN", type="password")
    if st.button("Entrar"):
        if pin == pin_cfg:
            st.session_state["viagem_auth_ok"] = True
            st.rerun()
        else:
            st.error("PIN incorreto.")
    return False


@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def sb():
    return get_supabase()


@st.cache_data(ttl=120)
def carregar_frota_veiculos():
    sup = sb()
    frota = sup.table("dim_frota").select("id_frota, modelo, categoria").eq("ativo", True).execute()
    painel = sup.table("dim_frota_painel").select("id_frota, modelo, categoria_painel").execute()
    df_f = pd.DataFrame(frota.data or [])
    df_p = pd.DataFrame(painel.data or [])
    cat_map = {}
    if not df_p.empty:
        for _, r in df_p.iterrows():
            cat_map[str(r["id_frota"]).strip()] = {
                "categoria": str(r.get("categoria_painel") or "").upper(),
                "modelo": r.get("modelo") or "",
            }
    veiculos = []
    for _, r in df_f.iterrows():
        fid = str(r["id_frota"]).strip()
        meta = cat_map.get(fid, {})
        cat = meta.get("categoria") or str(r.get("categoria") or "").upper()
        modelo = meta.get("modelo") or r.get("modelo") or ""
        if cat not in CATS_VEICULO:
            mod_u = str(modelo).upper()
            if any(x in mod_u for x in ("KWID", "TORO", "SAVEIRO", "STRADA", "HILUX", "RANGER", "S10")):
                cat = "VEICULO_LEVE"
            elif any(x in mod_u for x in ("MB", "2638", "SCANIA", "VOLVO", "CAMINH")):
                cat = "VEICULO_PESADO"
            elif any(x in mod_u for x in ("XRE", "CRF", "MOTO")):
                cat = "MOTO"
            else:
                continue
        linha = "LEVE" if cat in ("VEICULO_LEVE", "MOTO") else "PESADA"
        veiculos.append({
            "id_frota": fid,
            "modelo": modelo,
            "categoria": cat,
            "linha": linha,
            "label": f"{modelo} · {fid} [{linha}]" if modelo else f"{fid} [{linha}]",
        })
    veiculos.sort(key=lambda x: (x["linha"], x["label"]))
    return veiculos


@st.cache_data(ttl=300)
def carregar_retiros():
    try:
        res = sb().table("dim_retiro_fazenda").select("nome, lat, lng").eq("ativo", True).order("nome").execute()
        return res.data or []
    except Exception:
        return [
            {"nome": "SEDE / ESCRITÓRIO", "lat": -21.7167, "lng": -52.4217},
            {"nome": "OFICINA", "lat": -21.7175, "lng": -52.4225},
            {"nome": "DEPÓSITO / ALMOXARIFADO", "lat": -21.7180, "lng": -52.4210},
        ]


@st.cache_data(ttl=30)
def carregar_viagens(dias=90):
    try:
        res = (
            sb()
            .table("vw_viagem_veiculo_painel")
            .select("*")
            .gte("data_hora", (datetime.now() - timedelta(days=dias)).isoformat())
            .order("data_hora", desc=True)
            .limit(2000)
            .execute()
        )
        return pd.DataFrame(res.data or [])
    except Exception:
        res = (
            sb()
            .table("viagem_veiculo")
            .select("*")
            .gte("data_hora", (datetime.now() - timedelta(days=dias)).isoformat())
            .order("data_hora", desc=True)
            .limit(2000)
            .execute()
        )
        return pd.DataFrame(res.data or [])


def parse_dt(series):
    raw = series.astype(str).str.strip()
    has_tz = raw.str.contains(r"[+-]\d{2}:\d{2}|Z$", regex=True, na=False)
    dt = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    if has_tz.any():
        dt.loc[has_tz] = (
            pd.to_datetime(raw[has_tz], errors="coerce", utc=True)
            .dt.tz_convert("America/Sao_Paulo")
            .dt.tz_localize(None)
        )
    if (~has_tz).any():
        dt.loc[~has_tz] = pd.to_datetime(raw[~has_tz], errors="coerce")
    return dt


def mapa_externo(df_ext, height=420):
    m = folium.Map(location=list(FAZENDA_CENTER), zoom_start=6, tiles="OpenStreetMap")
    folium.Marker(
        list(FAZENDA_CENTER),
        popup="Base — Santa Vergínia",
        icon=folium.Icon(color="green", icon="home", prefix="fa"),
    ).add_to(m)
    if df_ext.empty:
        return m
    for _, row in df_ext.iterrows():
        lat, lng = row.get("destino_lat"), row.get("destino_lng")
        if pd.isna(lat) or pd.isna(lng):
            continue
        folium.Marker(
            [float(lat), float(lng)],
            popup=(
                f"{row.get('destino_cidade', '—')}<br>"
                f"Frota {row.get('id_frota')} · {row.get('km_percorrido', 0):.0f} km<br>"
                f"{row.get('motivo', '')}"
            ),
            icon=folium.Icon(color="blue", icon="car", prefix="fa"),
        ).add_to(m)
        folium.PolyLine(
            [list(FAZENDA_CENTER), [float(lat), float(lng)]],
            color="#4a9e3f", weight=2, opacity=0.6, dash_array="5",
        ).add_to(m)
    return m


def mapa_interno(retiros_data, viagens_int, height=420):
    m = folium.Map(location=list(FAZENDA_CENTER), zoom_start=14, tiles="OpenStreetMap")
    for r in retiros_data:
        lat, lng = r.get("lat"), r.get("lng")
        if lat is None or lng is None:
            continue
        folium.CircleMarker(
            [float(lat), float(lng)],
            radius=8,
            popup=r.get("nome", ""),
            color="#6fcf60",
            fill=True,
            fill_color="#4a9e3f",
            fill_opacity=0.8,
        ).add_to(m)
    if not viagens_int.empty:
        for _, row in viagens_int.iterrows():
            lat, lng = row.get("retiro_lat"), row.get("retiro_lng")
            if pd.isna(lat) or pd.isna(lng):
                continue
            folium.Marker(
                [float(lat), float(lng)],
                popup=f"Frota {row.get('id_frota')} · {row.get('motivo', '')}",
                icon=folium.Icon(color="orange", icon="info-sign"),
            ).add_to(m)
    return m


# ── Sidebar ──
with st.sidebar:
    st.markdown(f'<div class="logo-box"><img src="{LOGO_URL}" width="90"></div>', unsafe_allow_html=True)
    st.title("Controle de Viagens")
    st.caption(f"Build {PAINEL_BUILD}")
    menu = st.radio("Menu", ["📝 Lançar viagem", "📊 Painel", "🗺️ Mapas"], label_visibility="collapsed")
    st.divider()
    dias_filtro = st.slider("Período (dias)", 7, 180, 30)
    filtro_linha = st.multiselect("Linha", ["LEVE", "PESADA"], default=["LEVE", "PESADA"])
    st.caption("SIGCF | Santa Vergínia — MS")

if not exigir_pin():
    st.stop()

veiculos = carregar_frota_veiculos()
retiros_db = carregar_retiros()
df_v = carregar_viagens(dias_filtro)

if not df_v.empty and "data_hora" in df_v.columns:
    df_v["data_hora"] = parse_dt(df_v["data_hora"])
    df_v = df_v[df_v["linha"].isin(filtro_linha)] if "linha" in df_v.columns else df_v

# ═══════════════════════════════════════════════════════════════
# LANÇAR VIAGEM
# ═══════════════════════════════════════════════════════════════
if menu == "📝 Lançar viagem":
    col_logo, col_t = st.columns([1, 6])
    with col_logo:
        st.markdown(f'<div class="logo-box"><img src="{LOGO_URL}" width="80"></div>', unsafe_allow_html=True)
    with col_t:
        st.title("🚗 Lançamento de Viagem")
        st.caption("Veículos linha leve e pesada · viagem interna (fazenda) ou externa (cidade)")

    if not veiculos:
        st.warning("Nenhum veículo leve/pesado encontrado em dim_frota. Cadastre a frota no Supabase.")
        st.stop()

    tipo_viagem = st.radio(
        "Tipo de viagem",
        ["INTERNA — Local (fazenda)", "EXTERNA — Cidade"],
        horizontal=True,
        help="Interna: deslocamento entre retiros/setores. Externa: saída para cidade.",
    )
    eh_interna = tipo_viagem.startswith("INTERNA")

    with st.form("form_viagem", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            data_v = st.date_input("Data", value=date.today())
        with c2:
            hora_v = st.time_input("Hora", value=datetime.now().time().replace(second=0, microsecond=0))
        with c3:
            motorista = st.text_input("Motorista / condutor", placeholder="Nome do condutor")

        filtro_v = st.multiselect("Filtrar linha", ["LEVE", "PESADA"], default=["LEVE", "PESADA"])
        opts = [v["label"] for v in veiculos if v["linha"] in filtro_v] or [v["label"] for v in veiculos]
        veiculo_sel = st.selectbox("Veículo (frota)", options=opts)

        c4, c5 = st.columns(2)
        with c4:
            km_ini = st.number_input("KM inicial", min_value=0.0, step=0.1, format="%.1f")
        with c5:
            km_fim = st.number_input("KM final", min_value=0.0, step=0.1, format="%.1f")

        motivo_sel = st.selectbox("Motivo", MOTIVOS_PADRAO)
        motivo_extra = st.text_area(
            "Descreva o motivo",
            placeholder="Ex.: buscar rolamento na oficina de Bataguassu, levar mecânico ao retiro sul…",
            height=70,
        )

        destino_cidade = None
        dest_lat, dest_lng = None, None
        retiros_sel = []
        ret_lat, ret_lng = None, None

        if eh_interna:
            st.markdown('<div class="sec">📍 Retiros visitados (viagem interna)</div>', unsafe_allow_html=True)
            nomes_ret = [r["nome"] for r in retiros_db]
            retiros_sel = st.multiselect(
                "Selecione um ou mais retiros / setores",
                options=nomes_ret,
                help="Marque todos os pontos visitados na fazenda.",
            )
            if MAPA_FAZENDA.exists():
                st.image(str(MAPA_FAZENDA), caption="Mapa da fazenda — referência visual", use_container_width=True)
            else:
                st.info(
                    "Coloque o mapa da fazenda em `assets/mapa_fazenda.png` para exibir aqui. "
                    "Coordenadas dos retiros podem ser ajustadas no Supabase (dim_retiro_fazenda)."
                )
            if retiros_sel:
                primeiro = next((r for r in retiros_db if r["nome"] in retiros_sel), None)
                if primeiro:
                    ret_lat, ret_lng = primeiro.get("lat"), primeiro.get("lng")
        else:
            st.markdown('<div class="sec">🌍 Destino (viagem externa)</div>', unsafe_allow_html=True)
            destino_cidade = st.selectbox("Cidade / destino", CIDADES_COMUNS)
            destino_livre = st.text_input("Detalhe do destino (rua, fornecedor, bairro)")
            if destino_cidade == "Outra (informar abaixo)" and destino_livre:
                destino_cidade = destino_livre
            elif destino_livre:
                destino_cidade = f"{destino_cidade} — {destino_livre}"

        observacao = st.text_area("Observação adicional", height=60)
        enviar = st.form_submit_button("✅ REGISTRAR VIAGEM", use_container_width=True)

    if not eh_interna:
        st.markdown('<div class="sec">🗺️ Marque o destino no mapa (viagem externa)</div>', unsafe_allow_html=True)
        st.caption("Clique no mapa para registrar latitude/longitude do destino (opcional, complementa a cidade).")
        m_click = folium.Map(location=list(FAZENDA_CENTER), zoom_start=7)
        folium.Marker(list(FAZENDA_CENTER), popup="Base SV", icon=folium.Icon(color="green", icon="home")).add_to(m_click)
        if st.session_state.get("dest_coords"):
            lat0, lng0 = st.session_state.dest_coords
            folium.Marker([lat0, lng0], popup="Destino marcado", icon=folium.Icon(color="blue", icon="flag")).add_to(m_click)
        click = st_folium(m_click, height=350, returned_objects=["last_clicked"], key="mapa_destino_ext")
        if click and click.get("last_clicked"):
            st.session_state.dest_coords = (
                click["last_clicked"]["lat"],
                click["last_clicked"]["lng"],
            )
            st.success(
                f"Destino marcado: {st.session_state.dest_coords[0]:.5f}, "
                f"{st.session_state.dest_coords[1]:.5f}"
            )

    if enviar:
        if st.session_state.get("dest_coords") and not eh_interna:
            dest_lat, dest_lng = st.session_state.dest_coords
        erros = []
        if km_fim < km_ini:
            erros.append("KM final deve ser maior ou igual ao KM inicial.")
        motivo_final = motivo_extra.strip() if motivo_sel.startswith("Outro") else motivo_sel
        if motivo_extra.strip() and not motivo_sel.startswith("Outro"):
            motivo_final = f"{motivo_sel} — {motivo_extra.strip()}"
        if not motivo_final.strip():
            erros.append("Informe o motivo da viagem.")
        if eh_interna and not retiros_sel:
            erros.append("Selecione ao menos um retiro para viagem interna.")
        if not eh_interna and not destino_cidade:
            erros.append("Informe o destino da viagem externa.")

        if erros:
            for e in erros:
                st.error(f"❌ {e}")
        else:
            veic = next(v for v in veiculos if v["label"] == veiculo_sel)
            dt_hora = datetime.combine(data_v, hora_v)
            registro = {
                "data_hora": dt_hora.isoformat(),
                "id_frota": veic["id_frota"],
                "linha": veic["linha"],
                "km_inicial": float(km_ini),
                "km_final": float(km_fim),
                "tipo_viagem": "INTERNA" if eh_interna else "EXTERNA",
                "motivo": motivo_final.strip().upper(),
                "motorista": motorista.strip().upper() or None,
                "destino_cidade": destino_cidade if not eh_interna else None,
                "destino_lat": float(dest_lat) if dest_lat is not None else None,
                "destino_lng": float(dest_lng) if dest_lng is not None else None,
                "retiros": retiros_sel if eh_interna else None,
                "retiro_lat": float(ret_lat) if ret_lat is not None else None,
                "retiro_lng": float(ret_lng) if ret_lng is not None else None,
                "observacao": observacao.strip().upper() or None,
            }
            try:
                sb().table("viagem_veiculo").insert(registro).execute()
                km_p = km_fim - km_ini
                st.session_state.pop("dest_coords", None)
                st.success(
                    f"✅ Viagem registrada! {veic['id_frota']} · "
                    f"{'INTERNA' if eh_interna else 'EXTERNA'} · {km_p:.1f} km"
                )
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {e}")
                st.info("Confirme se rodou o SQL `criar_tabela_viagens.sql` no Supabase.")

    st.divider()
    st.markdown('<div class="sec">🕒 Últimas viagens</div>', unsafe_allow_html=True)
    if df_v.empty:
        st.info("Nenhuma viagem no período.")
    else:
        cols_show = ["data_hora", "id_frota", "linha", "tipo_viagem", "km_percorrido", "motivo"]
        if "destino_cidade" in df_v.columns:
            cols_show.append("destino_cidade")
        if "retiros" in df_v.columns:
            cols_show.append("retiros")
        vis = df_v.head(15).copy()
        vis["data_hora"] = vis["data_hora"].dt.strftime("%d/%m/%Y %H:%M")
        st.dataframe(vis[[c for c in cols_show if c in vis.columns]], use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════
# PAINEL
# ═══════════════════════════════════════════════════════════════
elif menu == "📊 Painel":
    st.title("📊 Painel de Viagens")
    st.caption(f"Período: últimos {dias_filtro} dias · Build {PAINEL_BUILD}")

    if df_v.empty:
        st.info("Sem viagens no período. Lance a primeira viagem na aba Lançar.")
        st.stop()

    km_total = float(df_v["km_percorrido"].sum()) if "km_percorrido" in df_v.columns else 0
    n_int = len(df_v[df_v["tipo_viagem"] == "INTERNA"]) if "tipo_viagem" in df_v.columns else 0
    n_ext = len(df_v[df_v["tipo_viagem"] == "EXTERNA"]) if "tipo_viagem" in df_v.columns else 0
    km_leve = float(df_v.loc[df_v["linha"] == "LEVE", "km_percorrido"].sum()) if "linha" in df_v.columns else 0
    km_pesada = float(df_v.loc[df_v["linha"] == "PESADA", "km_percorrido"].sum()) if "linha" in df_v.columns else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total viagens", len(df_v))
    m2.metric("KM percorridos", f"{km_total:,.0f}".replace(",", "."))
    m3.metric("Internas / Externas", f"{n_int} / {n_ext}")
    m4.metric("KM leve / pesada", f"{km_leve:.0f} / {km_pesada:.0f}")

    tab1, tab2, tab3, tab4 = st.tabs(["Por veículo", "Por motivo", "Linha do tempo", "Detalhado"])

    with tab1:
        if "id_frota" in df_v.columns:
            por_frota = (
                df_v.groupby("id_frota", as_index=False)
                .agg(viagens=("id", "count") if "id" in df_v.columns else ("km_percorrido", "count"), km=("km_percorrido", "sum"))
            )
            fig = px.bar(
                por_frota.sort_values("km", ascending=True).tail(15),
                x="km", y="id_frota", orientation="h",
                title="KM por frota (top 15)",
                color="km", color_continuous_scale=["#1e2e1c", "#4a9e3f"],
            )
            fig.update_layout(**PDARK, showlegend=False)
            fig.update_xaxes(**dict(gridcolor="#1e2e1c", tickfont=dict(color="#e8edd0")))
            fig.update_yaxes(**dict(gridcolor="#1e2e1c", tickfont=dict(color="#e8edd0")))
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if "motivo" in df_v.columns:
            por_motivo = df_v.groupby("motivo").size().reset_index(name="qtd").sort_values("qtd", ascending=False).head(12)
            fig2 = px.pie(
                por_motivo, names="motivo", values="qtd",
                title="Motivos mais frequentes",
                color_discrete_sequence=px.colors.sequential.Greens_r,
            )
            fig2.update_layout(**PDARK)
            st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        if "data_hora" in df_v.columns:
            df_d = df_v.copy()
            df_d["dia"] = df_d["data_hora"].dt.date
            por_dia = df_d.groupby(["dia", "tipo_viagem"], as_index=False)["km_percorrido"].sum()
            fig3 = px.bar(
                por_dia, x="dia", y="km_percorrido", color="tipo_viagem",
                title="KM por dia (interna vs externa)",
                color_discrete_map={"INTERNA": "#4a9e3f", "EXTERNA": "#5b9bd5"},
            )
            fig3.update_layout(**PDARK)
            st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        export = df_v.copy()
        if "data_hora" in export.columns:
            export["data_hora"] = export["data_hora"].dt.strftime("%d/%m/%Y %H:%M")
        st.dataframe(export, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════
# MAPAS
# ═══════════════════════════════════════════════════════════════
else:
    st.title("🗺️ Mapas interativos")
    if df_v.empty:
        st.info("Sem viagens para exibir no mapa.")
        st.stop()

    tab_ext, tab_int = st.tabs(["🌍 Viagens externas (cidade)", "🏡 Viagens internas (retiros)"])

    with tab_ext:
        df_ext = df_v[df_v["tipo_viagem"] == "EXTERNA"].copy() if "tipo_viagem" in df_v.columns else pd.DataFrame()
        st.caption(f"{len(df_ext)} viagens externas no período · linhas verdes = base → destino")
        st_folium(mapa_externo(df_ext), height=480, use_container_width=True)
        if not df_ext.empty and "destino_cidade" in df_ext.columns:
            destinos = df_ext.groupby("destino_cidade").agg(
                viagens=("id", "count") if "id" in df_ext.columns else ("km_percorrido", "count"),
                km=("km_percorrido", "sum"),
            ).reset_index().sort_values("viagens", ascending=False)
            st.dataframe(destinos, use_container_width=True, hide_index=True)

    with tab_int:
        df_int = df_v[df_v["tipo_viagem"] == "INTERNA"].copy() if "tipo_viagem" in df_v.columns else pd.DataFrame()
        c_img, c_map = st.columns([1, 1])
        with c_img:
            if MAPA_FAZENDA.exists():
                st.image(str(MAPA_FAZENDA), caption="Planta da fazenda", use_container_width=True)
            else:
                st.info("Adicione `assets/mapa_fazenda.png` para ver a planta ao lado do mapa.")
        with c_map:
            st.caption(f"{len(df_int)} viagens internas · círculos verdes = retiros cadastrados")
            st_folium(mapa_interno(retiros_db, df_int), height=400, use_container_width=True)

        if not df_int.empty and "retiros" in df_int.columns:
            all_ret = []
            for val in df_int["retiros"].dropna():
                if isinstance(val, list):
                    all_ret.extend(val)
            if all_ret:
                freq = pd.Series(all_ret).value_counts().reset_index()
                freq.columns = ["retiro", "visitas"]
                fig_r = px.bar(freq.head(12), x="visitas", y="retiro", orientation="h", title="Retiros mais visitados")
                fig_r.update_layout(**PDARK)
                st.plotly_chart(fig_r, use_container_width=True)

st.divider()
st.caption("SIGCF | Controle de Viagens SV | Controladoria Bataguassu-MS")

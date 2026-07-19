# -*- coding: utf-8 -*-
"""
SIG Frota de Veículos — APP DE LANÇAMENTO (campo)
Publicar como app.py no repo: controle-viagens-sv
"""
import streamlit as st
import pandas as pd
from datetime import date, datetime
from supabase import create_client

BUILD = "2026-07-19-lancamento-v8"

st.set_page_config(
    page_title="SIG Frota — Lançamento",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="collapsed",
)

try:
    from geografia import buscar_cidades
    from sigcf_auth import aplicar_tema_sigcf, dark_table, exigir_acesso, logo_html
except ImportError as exc:
    st.error(f"Dependência ausente no GitHub: {exc}")
    st.markdown(
        "Confira se estes arquivos estão **na raiz** do repositório (mesma pasta do app.py):\n\n"
        "- `sigcf_auth.py`\n"
        "- `geografia.py`\n\n"
        "Depois: **Manage app → Reboot app** no Streamlit Cloud."
    )
    st.stop()

exigir_acesso("SIG Frota de Veículos", "Lançamento de viagens — SIGCF Santa Virgínia")
aplicar_tema_sigcf()

MOTIVOS = [
    "Buscar material",
    "Levar colaborador",
    "Buscar peças / insumos",
    "Serviço em fornecedor",
    "Visita técnica",
    "Emergência / plantão",
    "Outro",
]

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


@st.cache_data(ttl=120)
def carregar_veiculos():
    res = (
        supabase.table("dim_veiculos")
        .select("placa, descricao, linha")
        .eq("ativo", True)
        .order("linha")
        .order("placa")
        .execute()
    )
    return res.data or []


@st.cache_data(ttl=300)
def carregar_locais_internos():
    res = (
        supabase.table("dim_locais")
        .select("nome")
        .eq("ativo", True)
        .eq("tipo", "INTERNO")
        .order("nome")
        .execute()
    )
    return [r["nome"] for r in (res.data or [])]


@st.cache_data(ttl=15)
def ultimas_viagens(limit=10):
    res = (
        supabase.table("viagem_veiculo")
        .select("data_hora, id_frota, tipo_viagem, km_percorrido, motivo, destino_cidade, retiros")
        .order("data_hora", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


veiculos = carregar_veiculos()
locais_int = carregar_locais_internos()

col_logo, col_titulo = st.columns([1.1, 5.9])
with col_logo:
    st.markdown(logo_html(118), unsafe_allow_html=True)
with col_titulo:
    st.markdown("## SIG Frota de Veículos")
    st.caption("Lançamento de viagens · SIGCF Santa Virgínia · Build " + BUILD)

if not veiculos:
    st.error("Cadastre veículos em dim_veiculos (rode sql/01_schema_sig_frota.sql no Supabase).")
    st.stop()

tipo_viagem = st.radio(
    "Tipo de viagem",
    ["INTERNA — Local (fazenda / retiros)", "EXTERNA — Cidade"],
    horizontal=True,
)
eh_interna = tipo_viagem.startswith("INTERNA")

destino_lat, destino_lng = None, None
destino_nome, destino_cidade = None, None

if not eh_interna:
    st.markdown('<div class="sec">Destino externo</div>', unsafe_allow_html=True)
    destino_livre = st.text_input(
        "Destino",
        placeholder="Ex: Sidrolândia, Campo Grande, fornecedor…",
    )
    destino_cidade = destino_livre.strip().upper() if destino_livre else None
    destino_nome = destino_cidade

st.markdown('<div class="sec">Registrar viagem</div>', unsafe_allow_html=True)

with st.form("form_viagem", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        data_v = st.date_input("📅 Data", value=date.today(), format="DD/MM/YYYY")
        motorista = st.text_input("Motorista / condutor")
        labels_veic = [f"{v['placa']} — {v['descricao']}" for v in veiculos]
        veic_sel = st.selectbox("Placa", labels_veic)
    with col2:
        km_ini = st.number_input("KM inicial", min_value=0.0, step=0.1, format="%.1f")
        km_fim = st.number_input("KM final", min_value=0.0, step=0.1, format="%.1f")
        km_calc = round(km_fim - km_ini, 1)
        if km_calc > 0:
            st.metric("KM percorridos", f"{km_calc:.1f} km")

    motivo = st.selectbox("Motivo", MOTIVOS)
    motivo_txt = st.text_input("Detalhe (se necessário)", placeholder="Opcional")

    locais_sel = []
    if eh_interna:
        locais_sel = st.multiselect("Retiros / locais visitados", options=locais_int)

    com_custos = st.checkbox("Informar custos da viagem (opcional)")
    litros = valor_abast = valor_ped = valor_manut = valor_mot = 0.0
    if com_custos:
        cc1, cc2 = st.columns(2)
        with cc1:
            litros = st.number_input("Litros", min_value=0.0, step=0.01, format="%.2f")
            valor_abast = st.number_input("Abastecimento (R$)", min_value=0.0, step=0.01, format="%.2f")
            valor_ped = st.number_input("Pedágio (R$)", min_value=0.0, step=0.01, format="%.2f")
        with cc2:
            valor_manut = st.number_input("Manutenção (R$)", min_value=0.0, step=0.01, format="%.2f")
            valor_mot = st.number_input("Motorista (R$)", min_value=0.0, step=0.01, format="%.2f")

    obs = st.text_input("Observação", placeholder="Opcional")
    enviar = st.form_submit_button("REGISTRAR VIAGEM", use_container_width=True, type="primary")

if enviar:
    placa = veic_sel.split(" — ")[0].strip().upper()
    motivo_final = motivo_txt.strip().upper() if motivo == "Outro" else motivo.upper()
    if motivo_txt.strip() and motivo != "Outro":
        motivo_final = f"{motivo.upper()} — {motivo_txt.strip().upper()}"

    agora = datetime.now()
    data_hora_viagem = datetime.combine(data_v, agora.time().replace(second=0, microsecond=0))

    erros = []
    if data_v > date.today():
        erros.append("Data não pode ser no futuro.")
    if km_fim < km_ini:
        erros.append("KM final deve ser ≥ KM inicial.")
    if not motivo_final:
        erros.append("Informe o motivo.")
    if eh_interna and not locais_sel:
        erros.append("Selecione ao menos um local interno.")
    if not eh_interna and not destino_cidade:
        erros.append("Informe o destino.")

    if erros:
        for e in erros:
            st.error(e)
    else:
        registro = {
            "data_hora": data_hora_viagem.isoformat(),
            "id_frota": placa,
            "linha": next(v["linha"] for v in veiculos if v["placa"] == placa),
            "km_inicial": float(km_ini),
            "km_final": float(km_fim),
            "tipo_viagem": "INTERNA" if eh_interna else "EXTERNA",
            "motivo": motivo_final,
            "motorista": motorista.strip().upper() or None,
            "retiros": locais_sel if eh_interna else None,
            "destino_nome": destino_nome if not eh_interna else None,
            "destino_cidade": destino_cidade if not eh_interna else None,
            "destino_lat": float(destino_lat) if destino_lat else None,
            "destino_lng": float(destino_lng) if destino_lng else None,
            "litros_abastecidos": float(litros) if litros > 0 else None,
            "valor_abastecimento": float(valor_abast) if valor_abast > 0 else None,
            "valor_pedagio": float(valor_ped) if valor_ped > 0 else None,
            "valor_manutencao": float(valor_manut) if valor_manut > 0 else None,
            "valor_motorista": float(valor_mot) if valor_mot > 0 else None,
            "observacao": obs.strip().upper() or None,
        }
        try:
            supabase.table("viagem_veiculo").insert(registro).execute()
            st.success(
                f"Viagem registrada — {placa} · {km_calc:.1f} km · "
                f"{data_hora_viagem.strftime('%d/%m/%Y %H:%M')}"
            )
            st.cache_data.clear()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

st.divider()
st.markdown('<div class="sec">Últimos lançamentos</div>', unsafe_allow_html=True)
rows = ultimas_viagens()
if rows:
    df = pd.DataFrame(rows)
    df["data_hora"] = pd.to_datetime(df["data_hora"], errors="coerce").dt.strftime("%d/%m/%Y %H:%M")
    df["destino"] = df.apply(
        lambda r: ", ".join(r["retiros"]) if r.get("retiros") else (r.get("destino_cidade") or "—"),
        axis=1,
    )
    dark_table(
        df[["data_hora", "id_frota", "tipo_viagem", "km_percorrido", "motivo", "destino"]].rename(
            columns={
                "data_hora": "Data/Hora",
                "id_frota": "Placa",
                "tipo_viagem": "Tipo",
                "km_percorrido": "KM",
                "motivo": "Motivo",
                "destino": "Destino",
            }
        )
    )
st.caption("SIG Frota de Veículos · Lançamento · Controladoria SV — MS")

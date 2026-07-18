# -*- coding: utf-8 -*-
"""
SIG Frota de Veículos — APP DE LANÇAMENTO (campo)
Publicar como app.py no repo: controle-viagens-sv
"""
import streamlit as st
import pandas as pd
from datetime import date, datetime
from supabase import create_client

from geografia import buscar_cidades
from sigcf_auth import aplicar_tema_sigcf, dark_table, exigir_acesso, logo_html

BUILD = "2026-07-18-lancamento-v3"

st.set_page_config(
    page_title="SIG Frota — Lançamento",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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


@st.cache_data(ttl=300)
def carregar_cidades_cadastradas():
    res = (
        supabase.table("dim_locais")
        .select("nome, lat, lng, cidade")
        .eq("ativo", True)
        .eq("tipo", "EXTERNO")
        .order("nome")
        .execute()
    )
    return res.data or []


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
cidades_db = carregar_cidades_cadastradas()

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
    c1, c2 = st.columns([2, 1])
    with c1:
        opcoes_cidade = [c["nome"] for c in cidades_db] + ["Buscar outra cidade (OpenStreetMap)..."]
        cidade_sel = st.selectbox("Cidade cadastrada", opcoes_cidade)
    with c2:
        busca_osm = st.text_input("Buscar cidade (OSM)", placeholder="Ex: Sidrolândia")

    if busca_osm.strip():
        resultados = buscar_cidades(busca_osm.strip())
        if resultados:
            labels = [r["label"] for r in resultados]
            escolha = st.selectbox("Resultado da busca", labels)
            if escolha:
                hit = next(r for r in resultados if r["label"] == escolha)
                destino_nome = hit["display_name"]
                destino_cidade = hit["label"]
                destino_lat, destino_lng = hit["lat"], hit["lng"]
                st.caption(f"Coordenadas: {destino_lat:.5f}, {destino_lng:.5f}")
        else:
            st.warning("Nenhum resultado. Tente outro nome.")

    if cidade_sel != "Buscar outra cidade (OpenStreetMap)..." and not destino_cidade:
        hit = next((c for c in cidades_db if c["nome"] == cidade_sel), None)
        if hit:
            destino_nome = hit["nome"]
            destino_cidade = hit.get("cidade") or hit["nome"]
            destino_lat = hit.get("lat")
            destino_lng = hit.get("lng")

st.markdown('<div class="sec">Registrar viagem</div>', unsafe_allow_html=True)

with st.form("form_viagem", clear_on_submit=True):
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        data_v = st.date_input("Data", value=date.today())
    with fc2:
        hora_v = st.time_input("Hora", value=datetime.now().time().replace(second=0, microsecond=0))
    with fc3:
        motorista = st.text_input("Motorista / condutor")

    labels_veic = [f"{v['placa']} — {v['descricao']}" for v in veiculos]
    veic_sel = st.selectbox("Placa", labels_veic)

    fc4, fc5 = st.columns(2)
    with fc4:
        km_ini = st.number_input("KM inicial", min_value=0.0, step=0.1, format="%.1f")
    with fc5:
        km_fim = st.number_input("KM final", min_value=0.0, step=0.1, format="%.1f")

    motivo = st.selectbox("Motivo", MOTIVOS)
    motivo_txt = st.text_area("Detalhe do motivo", height=60, placeholder="Descreva: buscar material, levar colaborador…")

    locais_sel = []
    if eh_interna:
        locais_sel = st.multiselect("Retiros / locais visitados", options=locais_int)

    with st.expander("Custos da viagem (opcional — entra no fechamento gerencial)"):
        cc1, cc2 = st.columns(2)
        with cc1:
            litros = st.number_input("Litros abastecidos", min_value=0.0, step=0.01, format="%.2f")
            valor_abast = st.number_input("Valor abastecimento (R$)", min_value=0.0, step=0.01, format="%.2f")
            valor_ped = st.number_input("Pedágio (R$)", min_value=0.0, step=0.01, format="%.2f")
        with cc2:
            valor_manut = st.number_input("Manutenção (R$)", min_value=0.0, step=0.01, format="%.2f")
            valor_mot = st.number_input("Valor motorista (R$)", min_value=0.0, step=0.01, format="%.2f")

    obs = st.text_area("Observação", height=50)
    enviar = st.form_submit_button("REGISTRAR VIAGEM", use_container_width=True, type="primary")

if enviar:
    placa = veic_sel.split(" — ")[0].strip().upper()
    motivo_final = motivo_txt.strip().upper() if motivo == "Outro" else motivo.upper()
    if motivo_txt.strip() and motivo != "Outro":
        motivo_final = f"{motivo.upper()} — {motivo_txt.strip().upper()}"

    erros = []
    if km_fim < km_ini:
        erros.append("KM final deve ser ≥ KM inicial.")
    if not motivo_final:
        erros.append("Informe o motivo.")
    if eh_interna and not locais_sel:
        erros.append("Selecione ao menos um local interno.")
    if not eh_interna and not destino_cidade and not destino_nome:
        erros.append("Selecione ou busque o destino externo.")

    if erros:
        for e in erros:
            st.error(e)
    else:
        registro = {
            "data_hora": datetime.combine(data_v, hora_v).isoformat(),
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
            st.success(f"Viagem registrada — {placa} · {km_fim - km_ini:.1f} km")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
            st.info("Execute sql/02_migrate_viagem_veiculo.sql no Supabase se ainda não rodou.")

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

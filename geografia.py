# -*- coding: utf-8 -*-
"""Geocodificação via Nominatim (OpenStreetMap) — API aberta, sem chave Google."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "SIGFrotaVeiculos-SV/1.0 (controladoria@santavirginia.local)"
NOMINATIM = "https://nominatim.openstreetmap.org"


def _get(url: str) -> list | dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def buscar_cidades(query: str, limit: int = 8) -> list[dict]:
    """Busca cidades/lugares no Brasil (Nominatim)."""
    q = (query or "").strip()
    if len(q) < 2:
        return []
    params = urllib.parse.urlencode({
        "q": f"{q}, Brasil",
        "format": "json",
        "addressdetails": 1,
        "limit": limit,
        "countrycodes": "br",
    })
    try:
        data = _get(f"{NOMINATIM}/search?{params}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []
    out = []
    for item in data or []:
        addr = item.get("address") or {}
        cidade = (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("municipality")
            or item.get("display_name", "").split(",")[0]
        )
        uf = addr.get("state", "")
        label = f"{cidade} — {uf}" if uf else item.get("display_name", cidade)
        out.append({
            "label": label.strip(),
            "lat": float(item["lat"]),
            "lng": float(item["lon"]),
            "display_name": item.get("display_name", label),
        })
    return out


def geocodificar_local(nome: str, cidade: str = "Bataguassu", uf: str = "MS") -> dict | None:
    """Geocodifica um local (retiro interno ou cidade)."""
    queries = [
        f"{nome}, Fazenda Santa Virgínia, {cidade}, {uf}, Brasil",
        f"{nome}, {cidade}, {uf}, Brasil",
        f"{nome}, Brasil",
    ]
    for q in queries:
        params = urllib.parse.urlencode({
            "q": q,
            "format": "json",
            "limit": 1,
            "countrycodes": "br",
        })
        try:
            data = _get(f"{NOMINATIM}/search?{params}")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            continue
        if data:
            item = data[0]
            return {
                "lat": float(item["lat"]),
                "lng": float(item["lon"]),
                "display_name": item.get("display_name", nome),
            }
    return None

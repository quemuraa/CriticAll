import html
import re

import requests
import streamlit as st

ANILIST_URL = "https://graphql.anilist.co"

SEARCH_QUERY = """
query ($search: String, $perPage: Int) {
  Page(perPage: $perPage) {
    media(search: $search, type: ANIME) {
      id
      title { romaji english }
      synonyms
      coverImage { large }
      seasonYear
      description
      popularity
      favourites
    }
  }
}
"""


def limpar_html(texto: str | None) -> str | None:
    """Remove tags HTML da sinopse da AniList."""
    if not texto:
        return None
    texto = re.sub(r"<br\s*/?>", " ", texto)
    texto = re.sub(r"<[^>]+>", "", texto)
    return html.unescape(texto).strip()


def buscar_bruto(termo: str, limite: int = 10) -> list[dict]:
    """Consulta a AniList e devolve o JSON cru."""
    corpo = {
        "query": SEARCH_QUERY,
        "variables": {"search": termo, "perPage": limite},
    }
    try:
        resposta = requests.post(ANILIST_URL, json=corpo, timeout=10)
        resposta.raise_for_status()
        return resposta.json()["data"]["Page"]["media"]
    except (requests.RequestException, KeyError, TypeError) as erro:
        st.error(f"Erro na busca AniList: {erro}")
        return []


def adaptar(media: dict) -> dict:
    """apicalypse -> criticall"""
    titulo = media["title"]["english"] or media["title"]["romaji"]
    capa = media.get("coverImage") or {}
    return {
        "source": "anilist",
        "source_id": str(media["id"]),
        "tipo": "anime",
        "titulo": titulo,
        "titulos_alternativos": media.get("synonyms") or [],
        "sinopse": limpar_html(media.get("description")),
        "capa_url": capa.get("large"),
        "ano_lancamento": media.get("seasonYear"), 
        "popularidade": media.get("popularity") or 0,
    }


def buscar(termo: str, limite: int = 10) -> list[dict]:
    """Busca e já devolve no formato interno."""
    return [adaptar(item) for item in buscar_bruto(termo, limite)]
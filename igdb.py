import streamlit as st
import requests
from datetime import datetime

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
IGDB_URL = "https://api.igdb.com/v4/games"


@st.cache_data(ttl=3600 * 24)
def obter_token_igdb() -> str | None:
    """Troca client_id + secret por um access token. Cacheado 24h."""
    try:
        resposta = requests.post(
            TWITCH_TOKEN_URL,
            params={
                "client_id": st.secrets["IGDB_CLIENT_ID"],
                "client_secret": st.secrets["IGDB_CLIENT_SECRET"],
                "grant_type": "client_credentials",
            },
            timeout=10,
        )
        resposta.raise_for_status()
        return resposta.json()["access_token"]
    except (requests.RequestException, KeyError) as erro:
        st.error(f"Falha ao autenticar na IGDB: {erro}")
        return None
    
IMG_BASE = "https://images.igdb.com/igdb/image/upload/t_cover_big/"


def buscar_igdb(termo: str, limite: int = 10) -> list[dict]:
    """Busca jogos na IGDB. Retorna lista crua da API (ainda não normalizada)."""
    token = obter_token_igdb()
    if not token:
        return []

    termo_limpo = termo.replace('"', "")

    corpo = (
        'fields name, summary, cover.image_id, first_release_date, '
        'genres.name, platforms.name, alternative_names.name, '
        'total_rating_count, rating, follows, hypes;'
        f'search "{termo_limpo}";'
        f'limit {limite};'
    )

    try:
        resposta = requests.post(
            IGDB_URL,
            headers={
                "Client-ID": st.secrets["IGDB_CLIENT_ID"],
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            data=corpo,
            timeout=10,
        )
        resposta.raise_for_status()
        return resposta.json()
    except requests.RequestException as erro:
        st.error(f"Erro na busca IGDB: {erro}")
        return []


def url_capa_igdb(jogo: dict) -> str | None:
    """Monta a URL da capa a partir do image_id. None se o jogo não tiver capa."""
    image_id = jogo.get("cover", {}).get("image_id")
    return f"{IMG_BASE}{image_id}.jpg" if image_id else None


def ano_lancamento_igdb(jogo: dict) -> int | None:
    """Converte o timestamp Unix da IGDB em ano."""
    ts = jogo.get("first_release_date")
    return datetime.fromtimestamp(ts).year if ts else None

def adaptar(jogo: dict) -> dict:
    """apicalypse -> criticall"""

    follows = jogo.get("follows") or 0
    ratings = jogo.get("total_rating_count") or 0
    popularidade = follows + ratings

    return {
        "source": "igdb",
        "source_id": str(jogo["id"]),
        "tipo": "jogo",
        "titulo": jogo["name"],
        "titulos_alternativos": [
            n["name"] for n in jogo.get("alternative_names", [])
        ],
        "sinopse": jogo.get("summary"),
        "capa_url": url_capa_igdb(jogo),
        "ano_lancamento": ano_lancamento_igdb(jogo),
        "popularidade": popularidade,
    }


def buscar(termo: str, limite: int = 10) -> list[dict]:
    """Busca e já devolve no formato interno."""
    return [adaptar(item) for item in buscar_igdb(termo, limite)]
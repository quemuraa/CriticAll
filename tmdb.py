import requests
import streamlit as st

TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
TMDB_TV_URL = "https://api.themoviedb.org/3/search/tv"
TMDB_MOVIE_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMG_BASE = "https://image.tmdb.org/t/p/w500"


def url_capa_tmdb(caminho: str | None) -> str | None:
    """Converte o poster_path do TMDB (só o caminho) em URL completa."""
    if not caminho:
        return None
    return f"{TMDB_IMG_BASE}{caminho}"


def ano_lancamento_tmdb(data_str: str | None) -> int | None:
    """Extrai o ano de uma data no formato 'AAAA-MM-DD'."""
    if not data_str:
        return None
    try:
        return int(data_str[:4])
    except (ValueError, IndexError):
        return None


def _buscar_bruto(url: str, termo: str, limite: int = 10) -> list[dict]:
    """Consulta um endpoint TMDB e devolve a lista bruta de resultados."""
    params = {
        "api_key": TMDB_API_KEY,
        "query": termo,
        "language": "pt-BR",
        "include_adult": False,
    }
    try:
        resposta = requests.get(url, params=params, timeout=10)
        resposta.raise_for_status()
        return resposta.json().get("results", [])[:limite]
    except (requests.RequestException, ValueError) as erro:
        st.error(f"Erro na busca TMDB: {erro}")
        return []


def adaptar_filme(filme: dict) -> dict:
    """Formato TMDB filme -> formato interno CriticAll."""
    titulo = filme.get("title") or ""
    titulo_original = filme.get("original_title") or ""
    
    alternativos = []
    if titulo_original and titulo_original != titulo:
        alternativos.append(titulo_original)
    
    return {
        "source": "tmdb",
        "source_id": str(filme["id"]),
        "tipo": "filme",
        "titulo": titulo,
        "titulos_alternativos": alternativos,
        "sinopse": filme.get("overview") or None,
        "capa_url": url_capa_tmdb(filme.get("poster_path")),
        "ano_lancamento": ano_lancamento_tmdb(filme.get("release_date")),
        "popularidade": filme.get("vote_count") or 0,
    }


def adaptar_serie(serie: dict) -> dict:
    """Formato TMDB série -> formato interno CriticAll."""
    titulo = serie.get("name") or ""
    titulo_original = serie.get("original_name") or ""
    
    alternativos = []
    if titulo_original and titulo_original != titulo:
        alternativos.append(titulo_original)
    
    return {
        "source": "tmdb",
        "source_id": str(serie["id"]),
        "tipo": "serie",
        "titulo": titulo,
        "titulos_alternativos": alternativos,
        "sinopse": serie.get("overview") or None,
        "capa_url": url_capa_tmdb(serie.get("poster_path")),
        "ano_lancamento": ano_lancamento_tmdb(serie.get("first_air_date")),
        "popularidade": serie.get("vote_count") or 0,
    }


def buscar_filmes(termo: str, limite: int = 10) -> list[dict]:
    """Busca filmes na TMDB e devolve no formato interno."""
    brutos = _buscar_bruto(TMDB_MOVIE_URL, termo, limite)
    return [adaptar_filme(item) for item in brutos]


def buscar_series(termo: str, limite: int = 10) -> list[dict]:
    """Busca séries na TMDB e devolve no formato interno."""
    brutos = _buscar_bruto(TMDB_TV_URL, termo, limite)
    return [adaptar_serie(item) for item in brutos]
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "criticall.db"


def get_conn():
    """Abre uma conexão com o banco de dados."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Cria a tabela 'obras' se ela ainda não existir."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS obras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_id TEXT NOT NULL,
                tipo TEXT NOT NULL,
                status TEXT NOT NULL,
                titulo TEXT NOT NULL,
                titulos_alternativos TEXT,
                sinopse TEXT,
                capa_url TEXT,
                ano_lancamento INTEGER,
                nota REAL,
                critica TEXT,
                data_consumo TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, source_id)
            )
        """)


def salvar_obra(
    source: str,
    source_id: str,
    tipo: str,
    status: str,
    titulo: str,
    titulos_alternativos: str,
    sinopse: str,
    capa_url: str,
    ano_lancamento: int,
    nota: float,
    critica: str,
    data_consumo: str,
):
    """
    Insere uma obra na biblioteca.
    Se já existir uma obra com o mesmo (source, source_id), ela é substituída.
    """
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM obras WHERE source = ? AND source_id = ?",
            (source, source_id)
        )
        conn.execute("""
            INSERT INTO obras (
                source, source_id, tipo, status, titulo, titulos_alternativos,
                sinopse, capa_url, ano_lancamento, nota, critica, data_consumo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source, source_id, tipo, status, titulo, titulos_alternativos,
            sinopse, capa_url, ano_lancamento, nota, critica, data_consumo,
        ))


def listar_obras():
    """Retorna todas as obras cadastradas, mais recentes primeiro."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM obras ORDER BY criado_em DESC")
        return [dict(linha) for linha in cursor.fetchall()]


def buscar_obra_por_source(source: str, source_id: str):
    """Retorna a obra com essa combinação (source, source_id), ou None se não existir."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM obras WHERE source = ? AND source_id = ?",
            (source, source_id)
        )
        linha = cursor.fetchone()
        return dict(linha) if linha else None
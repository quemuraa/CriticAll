import streamlit as st
import anilist
import igdb
import tmdb
import json
import math
from rapidfuzz import fuzz
from db import init_db, salvar_obra, listar_obras, buscar_obra_por_source
from datetime import date

FONTES = {
    "Anime": anilist.buscar,
    "Jogo": igdb.buscar,    
    "Filme": tmdb.buscar_filmes,
    "Série": tmdb.buscar_series,
}

# Fatores de normalização de popularidade por fonte.
# Calibrados empiricamente pra deixar valores comparáveis entre APIs.
FATORES_NORMALIZACAO = {
    "anime": 20000,  
    "jogo": 100,
    "filme": 5000,
    "serie": 5000,
}

init_db()  # Inicializa o banco de dados (cria a tabela se não existir)

st.set_page_config(page_title="CriticAll", layout="wide")

# CSS custom pro badge P5-inspired
st.markdown("""
    <style>
            
    h1 {
    font-family: 'Helvetica', sans-serif !important;
    }
            
            
    .nota-badge-container {
            text-align: center;
            margin-top: 25px;
    }
    .nota-badge {
        background-color: #FFFFFF;
        color: #111111;
        font-family: 'Franklin Gothic Medium', 'Helvetica', sans-serif;
        font-weight: 900;
        font-size: 64px;
        text-align: center;
        padding: 12px 24px;
        border-radius: 4px;
        box-shadow: 6px 6px 0 #DC2626;
        display: inline-block;
        margin: 8px 0 20px 0;
        letter-spacing: -2px;
    }
            
    .lib-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 8px;
        margin-bottom: 8px;
        min-height: 48px;
    }
    .lib-titulo {
        font-weight: 700;
        font-size: 13px;
        line-height: 1.2;
        color: #E5E5E5;
        flex: 1;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .lib-nota-mini {
        background-color: #FFFFFF;
        color: #111111;
        font-family: 'Franklin Gothic Medium', 'Helvetica', sans-serif;
        font-weight: 900;
        font-size: 16px;
        padding: 3px 8px;
        border-radius: 3px;
        box-shadow: 2px 2px 0 #DC2626;
        letter-spacing: -1px;
        flex-shrink: 0;
        height: fit-content;
    }
            
    .lib-capa {
    width: 100%;
    aspect-ratio: 2 / 3;
    object-fit: cover !important;
    border-radius: 4px;
    display: block;
    margin-bottom: 8px;
    }
            
    .stButton > button[kind="primary"] {
        background-color: #DC2626;
        border-color: #DC2626;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #B91C1C;
        border-color: #B91C1C;
    }
        
    
    </style>
""", unsafe_allow_html=True)



st.title("CriticAll")
st.write("Meu catálogo pessoal de tudo.")


def interpretar_nota(texto: str) -> float:
    """
    Converte o texto digitado pela pessoa em uma nota entre 0 e 10.
    Aceita: '9.8', '9,8', '98' (vira 9.8), '7' (vira 7.0).
    Retorna 7.0 como fallback se der ruim.
    """
    try:
        limpo = texto.replace(",", ".").strip()
        
        if "." not in limpo and len(limpo) == 2:
            nota = int(limpo) / 10
        else:
            nota = float(limpo)
        
        return max(0.0, min(10.0, nota))
    except (ValueError, AttributeError):
        return 7.0

def buscar_em_todas_fontes(
    termo: str,
    tipos_selecionados: list[str],
    limite_por_fonte: int = 10
) -> list[dict]:

    todos_resultados = []

    for nome_fonte in tipos_selecionados:

        funcao_busca = FONTES[nome_fonte]

        try:
            resultados = funcao_busca(
                termo,
                limite=limite_por_fonte
            )

            todos_resultados.extend(resultados)

        except Exception as erro:
            st.warning(
                f"Fonte '{nome_fonte}' falhou: {erro}"
            )


# Quero deixar o debug por enquanto, mas me solucione como eu posso colocar ele na mesma ordem que aparece na tela, ou seja, que ele não fique embaralhado..
    
    def similaridade(obra):
        titulo = obra["titulo"] or ""
        alternativos = obra.get("titulos_alternativos") or []
        popularidade = obra.get("popularidade") or 0
        tipo = obra.get("tipo", "")
        
        # Score textual (0-100)
        score_titulo = fuzz.WRatio(termo.lower(), titulo.lower())
        score_alt = 0
        if alternativos:
            scores_alt = [fuzz.WRatio(termo.lower(), a.lower()) for a in alternativos]
            score_alt = max(scores_alt) * 0.7
        score_textual = max(score_titulo, score_alt)
        
        # Score de popularidade absoluta, calibrado + log-suavizado
        fator = FATORES_NORMALIZACAO.get(tipo, 1)
        pop_calibrada = popularidade / fator
        score_pop = min(100, math.log(pop_calibrada + 1) * 25)
        
        # Combinação ponderada: 70% textual, 30% popularidade
        return score_textual * 0.7 + score_pop * 0.3

    
    todos_resultados.sort(key=similaridade, reverse=True)
    return todos_resultados

@st.dialog("Detalhes da obra", width="large")
def mostrar_detalhes(obra):
    titulo = obra["titulo"]
    capa = obra["capa_url"]
    ano = obra["ano_lancamento"] or "?"
    sinopse = obra["sinopse"] or "Sem sinopse disponível."
    
    # Busca no banco: essa obra já foi salva antes?
    obra_salva = buscar_obra_por_source(obra["source"], obra["source_id"])
    
    # Valores padrão do formulário
    if obra_salva:
        nota_inicial = f"{obra_salva['nota']:.1f}"
        critica_inicial = obra_salva["critica"] or ""
        # Extrai mês e ano da data salva (formato "AAAA-MM")
        try:
            ano_inicial, mes_inicial = obra_salva["data_consumo"].split("-")
            mes_inicial = int(mes_inicial)
            ano_inicial = int(ano_inicial)
        except (ValueError, AttributeError):
            mes_inicial = 1
            ano_inicial = date.today().year
        ja_cadastrada = True
    else:
        nota_inicial = "7.0"
        critica_inicial = ""
        mes_inicial = 1
        ano_inicial = date.today().year
        ja_cadastrada = False

    col_capa, col_info = st.columns([1, 3])

    with col_capa:
        st.image(capa, use_container_width=True)

    with col_info:
        st.subheader(titulo)
        st.caption(f"📅 {ano}")
        st.write(sinopse)
        
        if ja_cadastrada:
            st.info(f"📚 Você já cadastrou essa obra em {obra_salva['data_consumo']}. Editando abaixo.")

    
# Divisor entre informações e formulário
    st.divider()
    st.markdown("### ✍️ Adicionar à minha biblioteca")
    
    # Linha 1: badge da nota à esquerda, crítica à direita
    col_nota, col_critica = st.columns([1, 3])
    
    with col_nota:
        nota_atual_str = st.session_state.get(f"input_nota_{obra['source_id']}", nota_inicial)
        nota_atual = interpretar_nota(nota_atual_str)
        
        st.markdown(
            f'<div class="nota-badge-container"><div class="nota-badge">{nota_atual:.1f}</div></div>',
            unsafe_allow_html=True,
        )
    
    with col_critica:
        critica = st.text_area(
            "Sua crítica",
            placeholder="O que você achou da obra?",
            height=220,
            value=critica_inicial,
        )
    
    # Linha 2: nota + mês + ano — três colunas iguais
    col_nota_input, col_mes, col_ano = st.columns(3)
    
    with col_nota_input:
        nota_texto = st.text_input(
            "Nota (0-10)",
            value=nota_inicial,
            key=f"input_nota_{obra['source_id']}",
        )
        
        nota = interpretar_nota(nota_texto)
        
        # Se o texto for inválido (o fallback pegou), avisa
        if nota == 7.0 and nota_texto.strip() not in ["7", "7.0", "7,0", "70"]:
            st.caption("⚠️ Valor inválido, usando 7.0")
    
    with col_mes:
        mes_consumo = st.selectbox(
            "Mês de conclusão",
            options=list(range(1, 13)),
            index=mes_inicial - 1,
        )
    
    with col_ano:
        ano_consumo = st.number_input(
            "Ano de conclusão",
            min_value=1990,
            max_value=2040,
            value=ano_inicial,
            step=1,
        )
    
    # Debug: mostra o que foi selecionado (temporário)
    st.caption(f"🔧 Debug: nota={nota}, mês={mes_consumo}, ano={ano_consumo}")

# Botão salvar
    st.divider()
    
    if st.button("💾 Salvar na biblioteca", key=f"salvar_{obra['source_id']}", type="primary", use_container_width=True):
        titulo_salvar = obra["titulo"]
        capa_salvar = obra["capa_url"]
        ano_lancamento_salvar = obra["ano_lancamento"]
        
        data_consumo_formatada = f"{ano_consumo}-{mes_consumo:02d}"
        
        salvar_obra(
            source=obra["source"],
            source_id=obra["source_id"],
            tipo=obra["tipo"],
            status="watched",
            titulo=titulo_salvar,
            sinopse=sinopse,
            titulos_alternativos=json.dumps(obra.get("titulos_alternativos") or []),
            capa_url=capa_salvar,
            ano_lancamento=ano_lancamento_salvar,
            nota=nota,
            critica=critica,
            data_consumo=data_consumo_formatada,
        )
        
        st.success(f"✅ {titulo_salvar} adicionado à biblioteca!")

# Divide o app em duas abas
tab_buscar, tab_biblioteca = st.tabs(["🔍 Buscar", "📖 Minha biblioteca"])

with tab_buscar:
    st.write("Tipos de obra:")

    col_anime, col_jogo, col_filme, col_serie = st.columns(4)

    with col_anime:
        anime_selecionado = st.checkbox("Anime")

    with col_jogo:
        jogo_selecionado = st.checkbox("Jogo")

    with col_filme:
        filme_selecionado = st.checkbox("Filme")

    with col_serie:
        serie_selecionada = st.checkbox("Série")

    tipos_selecionados = []

    if anime_selecionado:
        tipos_selecionados.append("Anime")

    if jogo_selecionado:
        tipos_selecionados.append("Jogo")

    if filme_selecionado:
        tipos_selecionados.append("Filme")

    if serie_selecionada:
        tipos_selecionados.append("Série")

    query = st.text_input("Buscar obra:")
    
    if query and not tipos_selecionados:
        st.warning("Selecione pelo menos um tipo de obra.")

    elif query and tipos_selecionados:
        obras_encontradas = buscar_em_todas_fontes(
            query,
            tipos_selecionados,
            limite_por_fonte=25
        )
    
        if len(obras_encontradas) == 0:
            st.warning("Nenhuma obra encontrada.")
        else:
            st.success(f"{len(obras_encontradas)} obra(s) encontrada(s).")

            obras_encontradas = obras_encontradas[:15]
            st.caption(f"{len(obras_encontradas)} resultado(s)")

            for obra in obras_encontradas:
                titulo = obra["titulo"]
                ano = obra["ano_lancamento"] or "?"
                capa = obra["capa_url"]
                sinopse = obra["sinopse"] or "Sem sinopse..."
                sinonimos = obra.get("titulos_alternativos", [])

                col_capa, col_info = st.columns([1, 5])
                with col_capa:
                    if capa:
                        st.image(capa, use_container_width=True)
                    else:
                        st.markdown("*(sem capa)*")
                with col_info:
                    st.subheader(titulo)
                    st.caption(f"📅 {ano} · 🏷️ {obra['tipo'].capitalize()}")
                    if sinonimos:
                        st.caption(f"🔤 Também conhecido como: {', '.join(sinonimos[:5])}")
                    st.write(sinopse)
                    if st.button("📖 Ver detalhes", key=f"btn_{obra['source']}_{obra['source_id']}"):
                        mostrar_detalhes(obra)

                st.divider()

with tab_biblioteca:
    obras = listar_obras()
    
    if len(obras) == 0:
        st.info("📭 Você ainda não cadastrou nenhuma obra. Vai lá na aba Buscar e adiciona a primeira!")
    else:
        # Filtro por tipo (chips)
        tipos_biblioteca = ["Todos"] + sorted({obra["tipo"].capitalize() for obra in obras})
        tipo_lib_selecionado = st.radio(
            "Filtrar por tipo:",
            options=tipos_biblioteca,
            horizontal=True,
            label_visibility="collapsed",
            key="filtro_biblioteca",
        )
        
        # Aplica o filtro
        if tipo_lib_selecionado != "Todos":
            obras = [obra for obra in obras if obra["tipo"].capitalize() == tipo_lib_selecionado]
        
        st.caption(f"Você tem {len(obras)} obra(s) cadastrada(s).")
        st.divider()
        
        colunas_por_linha = 8
        
        for i in range(0, len(obras), colunas_por_linha):
            colunas = st.columns(colunas_por_linha)
            
            for j, coluna in enumerate(colunas):
                if i + j < len(obras):
                    obra = obras[i + j]
                    with coluna:
                        st.markdown(
                            f"""
                            <div class="lib-header">
                                <div class="lib-titulo">{obra['titulo']}</div>
                                <div class="lib-nota-mini">{obra['nota']:.1f}</div>
                            </div>
                            <img class="lib-capa" src="{obra['capa_url']}">
                            """,
                            unsafe_allow_html=True,
                        )
                        
                        if st.button("📖 Detalhes", key=f"lib_btn_{obra['id']}", use_container_width=True):
                            mostrar_detalhes(obra)
    

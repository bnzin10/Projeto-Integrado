"""Painel integrado: indicadores socioeconômicos e demográficos do IBGE.
Executar a partir desta pasta com: python -m streamlit run painel.py
Cada dashboard é uma página independente em paginas/.
"""
import streamlit as st

st.set_page_config(
    page_title="Números que Falam | Painel IBGE",
    page_icon="📊",
    layout="wide",
)


def inicio():
    st.title("📊 Números que Falam — Descobrindo o Brasil")
    st.write(
        "Painel integrado de indicadores do IBGE com análises estatísticas. "
        "Escolha uma das cinco páginas pelo menu lateral ou abra abaixo."
    )
    st.caption("As páginas possuem filtros independentes e preservam seus gráficos e análises.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("📉 Desocupação por UF")
        st.write("PNAD Contínua: taxas por estado, medidas descritivas e outliers.")
        st.page_link(pag_desocupacao, label="Abrir desocupação", icon="📉")
    with c2:
        st.subheader("👥 Estrutura etária")
        st.write("Censo 2022: pirâmide etária por sexo e cor ou raça.")
        st.page_link(pag_idade, label="Abrir estrutura etária", icon="👥")
    with c3:
        st.subheader("📚 Alfabetização")
        st.write("Análise por sexo, raça, região e idade com **dados ilustrativos**.")
        st.page_link(pag_alfa, label="Abrir alfabetização", icon="📚")

    st.divider()
    c4, c5 = st.columns(2)
    with c4:
        st.subheader("👩 População feminina")
        st.write("IBGE/SIDRA, Censo 2022: distribuição, comparações territoriais, "
                 "estatísticas e gráficos, incluindo boxplot.")
        st.page_link(pag_individual, label="Abrir população feminina", icon="👩")
    with c5:
        st.subheader("💰 Rendimento dos responsáveis")
        st.write("Censo 2022: boxplot de rendimento por UF, quartis, dispersão e outliers.")
        st.page_link(pag_rendimento, label="Abrir rendimentos", icon="💰")

    st.info("As páginas de população feminina, estrutura etária e rendimento "
            "consultam dados públicos pela internet. A página de população feminina "
            "pode recorrer a valores aproximados quando a API estiver indisponível.")
    st.caption("Fontes: IBGE / SIDRA, PNAD Contínua e Censo Demográfico 2022.")


pag_inicio = st.Page(inicio, title="Início", icon="🏠", default=True)
pag_desocupacao = st.Page("paginas/desocupacao.py", title="Desocupação por UF", icon="📉")
pag_idade = st.Page("paginas/estrutura_etaria.py", title="Estrutura etária", icon="👥")
pag_alfa = st.Page("paginas/alfabetizacao.py", title="Alfabetização", icon="📚")
pag_individual = st.Page("paginas/dashboard_individual.py", title="População feminina", icon="👩")
pag_rendimento = st.Page("paginas/dashboard_rendimento_boxplot.py", title="Rendimento (boxplot)", icon="💰")

st.navigation([
    pag_inicio,
    pag_desocupacao,
    pag_idade,
    pag_alfa,
    pag_individual,
    pag_rendimento,
]).run()

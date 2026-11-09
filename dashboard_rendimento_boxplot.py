"""Dashboard individual: Rendimento dos responsáveis pelo domicílio (IBGE 2022).
Execute com: py -m streamlit run dashboard_rendimento_boxplot.py
"""
import io
import zipfile
import requests
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

URL_IBGE = (
    "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/"
    "Agregados_por_Setores_Censitarios_Rendimento_do_Responsavel/"
    "Agregados_por_setores_renda_responsavel_BR_20260508_csv.zip"
)

UF_INFO = {
    "11": ("Rondônia", "Norte"), "12": ("Acre", "Norte"),
    "13": ("Amazonas", "Norte"), "14": ("Roraima", "Norte"),
    "15": ("Pará", "Norte"), "16": ("Amapá", "Norte"),
    "17": ("Tocantins", "Norte"),
    "21": ("Maranhão", "Nordeste"), "22": ("Piauí", "Nordeste"),
    "23": ("Ceará", "Nordeste"), "24": ("Rio Grande do Norte", "Nordeste"),
    "25": ("Paraíba", "Nordeste"), "26": ("Pernambuco", "Nordeste"),
    "27": ("Alagoas", "Nordeste"), "28": ("Sergipe", "Nordeste"),
    "29": ("Bahia", "Nordeste"),
    "31": ("Minas Gerais", "Sudeste"), "32": ("Espírito Santo", "Sudeste"),
    "33": ("Rio de Janeiro", "Sudeste"), "35": ("São Paulo", "Sudeste"),
    "41": ("Paraná", "Sul"), "42": ("Santa Catarina", "Sul"),
    "43": ("Rio Grande do Sul", "Sul"),
    "50": ("Mato Grosso do Sul", "Centro-Oeste"),
    "51": ("Mato Grosso", "Centro-Oeste"), "52": ("Goiás", "Centro-Oeste"),
    "53": ("Distrito Federal", "Centro-Oeste"),
}

def _achar_coluna(colunas, nomes):
    mapa = {str(c).strip().upper(): c for c in colunas}
    for nome in nomes:
        if nome.upper() in mapa:
            return mapa[nome.upper()]
    return None

@st.cache_data(show_spinner=False)
def carregar_base_ibge():
    resposta = requests.get(URL_IBGE, timeout=180)
    resposta.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resposta.content)) as arquivo_zip:
        arquivos_csv = [n for n in arquivo_zip.namelist() if n.lower().endswith(".csv")]
        if not arquivos_csv:
            raise ValueError("O ZIP baixado não contém um arquivo CSV.")
        with arquivo_zip.open(arquivos_csv[0]) as arquivo:
            dados_brutos = pd.read_csv(
                arquivo, sep=";", dtype=str, encoding="utf-8-sig", low_memory=False
            )

    dados_brutos.columns = [str(c).strip().replace('"', '') for c in dados_brutos.columns]
    col_setor = _achar_coluna(dados_brutos.columns, ["CD_SETOR"])
    col_quantidade = _achar_coluna(dados_brutos.columns, ["V06001"])
    col_rendimento = _achar_coluna(dados_brutos.columns, ["V06004"])

    faltantes = [
        nome for nome, coluna in [
            ("CD_SETOR", col_setor),
            ("V06001", col_quantidade),
            ("V06004", col_rendimento)
        ] if coluna is None
    ]
    if faltantes:
        raise ValueError(
            "Não foram encontradas as colunas: " + ", ".join(faltantes) +
            ". Confira o arquivo e o dicionário de dados do IBGE."
        )

    df = pd.DataFrame({
        "codigo_setor": dados_brutos[col_setor].astype(str).str.replace(r"\D", "", regex=True),
        "quantidade_responsaveis": pd.to_numeric(dados_brutos[col_quantidade], errors="coerce"),
        "rendimento_medio": pd.to_numeric(dados_brutos[col_rendimento], errors="coerce")
    })

    df = df[
        (df["codigo_setor"].str.len() >= 2)
        & df["quantidade_responsaveis"].notna()
        & (df["quantidade_responsaveis"] > 0)
        & df["rendimento_medio"].notna()
        & (df["rendimento_medio"] > 0)
    ].copy()

    df["codigo_uf"] = df["codigo_setor"].str[:2]
    df["uf"] = df["codigo_uf"].map(lambda c: UF_INFO.get(c, ("UF não identificada", ""))[0])
    df["regiao"] = df["codigo_uf"].map(lambda c: UF_INFO.get(c, ("", "Não identificada"))[1])
    df = df[df["regiao"] != "Não identificada"].copy()
    return df

def _reais(valor):
    return ("R$ " + f"{valor:,.2f}").replace(",", "X").replace(".", ",").replace("X", ".")

def renderizar():
    st.title("Rendimento dos responsáveis pelo domicílio")
    st.write(
        "Análise da distribuição dos rendimentos nominais médios mensais "
        "dos responsáveis pelos domicílios, com dados do Censo Demográfico 2022."
    )

    st.info(
        "**Indicador utilizado:** V06004 — rendimento nominal médio mensal das pessoas "
        "responsáveis pelo domicílio que tinham rendimento, por setor censitário. "
        "A variável V06001 informa a quantidade de responsáveis e é usada como peso "
        "na média ponderada. Este indicador não é renda domiciliar per capita."
    )

    with st.spinner("Carregando os dados oficiais do IBGE..."):
        try:
            dados = carregar_base_ibge()
        except Exception as erro:
            st.error(f"Não foi possível carregar a base do IBGE: {erro}")
            st.markdown(f"[Acessar a pasta oficial de downloads do IBGE]({URL_IBGE})")
            st.stop()

    st.sidebar.subheader("Filtros da análise")
    regioes = ["Brasil"] + sorted(dados["regiao"].unique().tolist())
    regiao = st.sidebar.selectbox("Região", regioes, key="rendimento_regiao")

    filtrado = dados.copy()
    if regiao != "Brasil":
        filtrado = filtrado[filtrado["regiao"] == regiao]

    lista_ufs = ["Todas"] + sorted(filtrado["uf"].unique().tolist())
    uf = st.sidebar.selectbox("Estado", lista_ufs, key="rendimento_uf")
    if uf != "Todas":
        filtrado = filtrado[filtrado["uf"] == uf]

    valores = filtrado["rendimento_medio"].dropna()
    if valores.empty:
        st.warning("Não existem dados para os filtros selecionados.")
        return

    q1 = valores.quantile(0.25)
    mediana = valores.median()
    q3 = valores.quantile(0.75)
    iqr = q3 - q1
    limite_inf = q1 - 1.5 * iqr
    limite_sup = q3 + 1.5 * iqr
    outliers = filtrado[
        (filtrado["rendimento_medio"] < limite_inf)
        | (filtrado["rendimento_medio"] > limite_sup)
    ]
    media = valores.mean()
    media_ponderada = np.average(
        filtrado["rendimento_medio"],
        weights=filtrado["quantidade_responsaveis"]
    )
    desvio = valores.std(ddof=1)
    amplitude = valores.max() - valores.min()
    moda = valores.mode()
    moda_valor = _reais(moda.iloc[0]) if len(moda) and valores.value_counts().max() > 1 else "Não há moda única"

    st.caption(
        f"Observações: {len(valores):,} setores censitários | "
        f"Responsáveis com rendimento representados: "
        f"{filtrado['quantidade_responsaveis'].sum():,.0f}".replace(",", ".")
    )

    a, b, c, d = st.columns(4)
    a.metric("Média", _reais(media))
    b.metric("Mediana (Q2)", _reais(mediana))
    c.metric("IQR", _reais(iqr))
    d.metric("Outliers", f"{len(outliers):,}".replace(",", "."))

    st.divider()
    st.subheader("Boxplot — distribuição dos rendimentos")
    st.write(
        "Cada caixa representa a distribuição dos rendimentos médios dos setores "
        "censitários. A linha dentro da caixa é a mediana; as extremidades da caixa "
        "representam Q1 e Q3; os pontos além dos limites são possíveis outliers."
    )

    if uf == "Todas":
        fig = px.box(
            filtrado,
            x="uf",
            y="rendimento_medio",
            color="regiao",
            points="outliers",
            category_orders={"uf": sorted(filtrado["uf"].unique())},
            labels={
                "uf": "Unidade da Federação",
                "rendimento_medio": "Rendimento médio mensal (R$)",
                "regiao": "Região"
            },
            title="Boxplot dos rendimentos por Unidade da Federação"
        )
        fig.update_layout(xaxis_tickangle=-45, legend_title_text="Região")
    else:
        fig = px.box(
            filtrado,
            y="rendimento_medio",
            points="outliers",
            labels={"rendimento_medio": "Rendimento médio mensal (R$)"},
            title=f"Boxplot dos rendimentos dos setores censitários — {uf}"
        )
    fig.update_layout(
        yaxis_title="Rendimento nominal médio mensal (R$)",
        xaxis_title="",
        showlegend=(uf == "Todas")
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Medidas estatísticas")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Tendência central**")
        st.write(f"- Média: **{_reais(media)}**")
        st.write(f"- Mediana (Q2): **{_reais(mediana)}**")
        st.write(f"- Moda: **{moda_valor}**")
        st.write(f"- Média ponderada por responsáveis: **{_reais(media_ponderada)}**")
    with col2:
        st.markdown("**Dispersão e quartis**")
        st.write(f"- Q1: **{_reais(q1)}**")
        st.write(f"- Q3: **{_reais(q3)}**")
        st.write(f"- IQR: **{_reais(iqr)}**")
        st.write(f"- Amplitude: **{_reais(amplitude)}**")
        st.write(f"- Desvio padrão amostral: **{_reais(desvio)}**")

    st.write(f"- Variância amostral: **{valores.var(ddof=1):,.2f} R$²**")
    st.write(f"- Limite inferior para outliers: **{_reais(limite_inf)}**")
    st.write(f"- Limite superior para outliers: **{_reais(limite_sup)}**")

    st.divider()
    st.subheader("Interpretação dos resultados")
    if media > mediana:
        st.write(
            "A média está acima da mediana. Isso sugere assimetria à direita: "
            "alguns setores com rendimentos mais altos podem elevar a média. "
            "Por isso, a mediana pode representar melhor o centro da distribuição."
        )
    elif media < mediana:
        st.write(
            "A média está abaixo da mediana. Isso pode indicar influência de setores "
            "com rendimentos menores sobre o valor médio."
        )
    else:
        st.write("A média e a mediana são iguais ou muito próximas.")

    st.write(
        f"Os 50% centrais dos setores apresentam rendimentos entre "
        f"**{_reais(q1)} (Q1)** e **{_reais(q3)} (Q3)**. "
        f"A distância entre esses quartis é de **{_reais(iqr)}**, que corresponde ao IQR."
    )
    st.write(
        f"Pela regra de 1,5 × IQR, foram identificados **{len(outliers):,} possíveis outliers**. "
        "Eles são observações territoriais atípicas e não devem ser considerados erros "
        "automaticamente."
    )

    st.warning(
        "Atenção: as medidas e o boxplot descrevem a distribuição dos rendimentos médios "
        "dos setores censitários, não a renda individual de cada brasileiro. "
        "A variável V06004 considera somente responsáveis com rendimento."
    )

    st.caption(
        "Fonte: IBGE — Censo Demográfico 2022, Agregados por Setores Censitários, "
        "Rendimento do Responsável pelo Domicílio. Variáveis V06001 e V06004. "
        "Valores nominais de referência de 2022."
    )

# Executado pelo st.navigation() do painel principal.
renderizar()

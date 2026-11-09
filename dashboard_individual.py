"""Página integrada ao painel: população feminina no Brasil (IBGE/SIDRA)."""
# Dashboard: População Feminina no Brasil — recortes e comparações territoriais
# Fonte: IBGE / SIDRA — Censo Demográfico 2022 (Tabela 9514)
import re

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st



# ---------------------------------------------------------------- Estilo ----
BG, CARD, TXT = "#0F1B33", "#16254A", "#E6ECF8"
ROSA, AZUL, VERDE, LARANJA = "#F06292", "#5B9BEF", "#2ECC71", "#F5A623"

st.markdown(
    f"""
<style>
.stApp {{ background:{BG}; color:{TXT}; }}
[data-testid="stSidebar"] {{ background:{CARD}; }}
h1,h2,h3,h4,p,label,span {{ color:{TXT}; }}
.card {{ background:{CARD}; border-radius:12px; padding:16px 18px; border:1px solid #22345F; }}
.card .t {{ font-size:.85rem; color:#9FB0D3; margin-bottom:2px; }}
.card .s {{ font-size:.7rem; color:#6F82AD; margin-bottom:8px; }}
.card .v {{ font-size:2rem; font-weight:700; }}
.card .d {{ font-size:.8rem; color:#9FB0D3; }}
</style>
""",
    unsafe_allow_html=True,
)


def kpi(titulo, valor, cor, detalhe=""):
    st.markdown(
        f"""<div class="card"><div class="t">{titulo}</div>
        <div class="s">Censo 2022</div>
        <div class="v" style="color:{cor}">{valor}</div>
        <div class="d">{detalhe}</div></div>""",
        unsafe_allow_html=True,
    )


def estilo(fig, h=360):
    fig.update_layout(
        paper_bgcolor=CARD, plot_bgcolor=CARD, font_color=TXT, height=h,
        margin=dict(l=10, r=10, t=45, b=10), legend_title_text="",
    )
    fig.update_xaxes(gridcolor="#22345F")
    fig.update_yaxes(gridcolor="#22345F")
    return fig


# ------------------------------------------------------------------ Dados ----
REGIAO = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}
SIDRA = "https://apisidra.ibge.gov.br/values/t/9514/{terr}/v/93/p/2022/c2/4,5/c286/113635/c287/{idade}"

# Dados aproximados usados SOMENTE se a API do IBGE estiver indisponível.
# (cod, sigla, nome, população total, % feminina aproximada)
FALLBACK = [
    (11, "RO", "Rondônia", 1581196, 49.6), (12, "AC", "Acre", 830018, 50.1),
    (13, "AM", "Amazonas", 3941613, 50.3), (14, "RR", "Roraima", 636707, 49.5),
    (15, "PA", "Pará", 8120131, 50.2), (16, "AP", "Amapá", 733759, 50.5),
    (17, "TO", "Tocantins", 1511460, 49.9), (21, "MA", "Maranhão", 6776699, 51.0),
    (22, "PI", "Piauí", 3271199, 51.8), (23, "CE", "Ceará", 8794957, 52.0),
    (24, "RN", "Rio Grande do Norte", 3302729, 51.6), (25, "PB", "Paraíba", 3974687, 51.9),
    (26, "PE", "Pernambuco", 9058931, 52.6), (27, "AL", "Alagoas", 3127683, 52.0),
    (28, "SE", "Sergipe", 2210004, 51.8), (29, "BA", "Bahia", 14141626, 51.9),
    (31, "MG", "Minas Gerais", 20538718, 51.3), (32, "ES", "Espírito Santo", 3833712, 51.4),
    (33, "RJ", "Rio de Janeiro", 16055174, 52.7), (35, "SP", "São Paulo", 44411238, 51.8),
    (41, "PR", "Paraná", 11444380, 51.2), (42, "SC", "Santa Catarina", 7610361, 50.5),
    (43, "RS", "Rio Grande do Sul", 10882965, 51.7), (50, "MS", "Mato Grosso do Sul", 2757013, 50.3),
    (51, "MT", "Mato Grosso", 3658649, 49.7), (52, "GO", "Goiás", 7056495, 50.8),
    (53, "DF", "Distrito Federal", 2817381, 52.9),
]
SIGLAS = {n: s for _, s, n, _, _ in FALLBACK}


def _sidra(terr, idade):
    """Baixa a tabela e devolve DataFrame com colunas: local, cod, sexo, idade, valor."""
    r = requests.get(SIDRA.format(terr=terr, idade=idade), timeout=60)
    r.raise_for_status()
    dados = r.json()
    cab, linhas = dados[0], dados[1:]
    chave = lambda txt: next(k for k, v in cab.items() if k.endswith("N") and txt in v)
    k_terr = next(k for k, v in cab.items() if k.endswith("N") and v in ("Brasil", "Unidade da Federação"))
    k_sexo, k_idade = chave("Sexo"), chave("Idade")
    k_terr_c = k_terr[:-1] + "C"
    df = pd.DataFrame(
        {
            "local": [l[k_terr] for l in linhas],
            "cod": [l[k_terr_c] for l in linhas],
            "sexo": [l[k_sexo] for l in linhas],
            "idade": [l[k_idade] for l in linhas],
            "valor": pd.to_numeric([l["V"] for l in linhas], errors="coerce"),
        }
    )
    return df.dropna(subset=["valor"])


@st.cache_data(ttl=86400, show_spinner="Consultando a API SIDRA do IBGE...")
def carregar_ufs():
    try:
        df = _sidra("n3/all", "100362")  # 100362 = idade total
        p = df.pivot_table(index=["cod", "local"], columns="sexo", values="valor", aggfunc="sum").reset_index()
        p = p.rename(columns={"Mulheres": "mulheres", "Homens": "homens", "local": "uf"})
        fonte = "API SIDRA/IBGE (Tabela 9514, Censo 2022)"
    except Exception:
        p = pd.DataFrame(
            [(str(c), n, round(t * pf / 100), round(t * (100 - pf) / 100)) for c, _, n, t, pf in FALLBACK],
            columns=["cod", "uf", "mulheres", "homens"],
        )
        fonte = "Dados APROXIMADOS offline (sem conexão com a API do IBGE)"
    p["sigla"] = p["uf"].map(SIGLAS)
    p["regiao"] = p["cod"].astype(str).str[0].map(REGIAO)
    p["total"] = p["mulheres"] + p["homens"]
    p["pct_mulheres"] = p["mulheres"] / p["total"] * 100
    p["razao_sexo"] = p["homens"] / p["mulheres"] * 100  # homens por 100 mulheres
    return p, fonte


@st.cache_data(ttl=86400, show_spinner="Carregando pirâmide etária...")
def carregar_piramide():
    try:
        df = _sidra("n1/1", "all")

        def idade(txt):
            if txt.lower().startswith("menos de 1"):
                return 0
            m = re.fullmatch(r"(\d+) anos?( ou mais)?", txt.strip())
            return int(m.group(1)) if m else None

        df["anos"] = df["idade"].map(idade)
        df = df.dropna(subset=["anos"])
        df["faixa"] = (df["anos"].clip(upper=85) // 5 * 5).astype(int)
        g = df.groupby(["faixa", "sexo"])["valor"].sum().reset_index()
        g["rotulo"] = g["faixa"].map(lambda f: "85+" if f == 85 else f"{f}-{f+4}")
        return g
    except Exception:
        return None


ufs, fonte = carregar_ufs()
assert ufs is not None, "Falha ao carregar dados — verifique se o arquivo foi copiado por inteiro."

# ----------------------------------------------------------------- Filtros ----
st.sidebar.title("Filtros")
regioes = st.sidebar.multiselect("Região", list(REGIAO.values()), default=list(REGIAO.values()))
metrica = st.sidebar.radio(
    "Indicador do ranking",
    ["% de mulheres", "Mulheres (absoluto)", "Homens por 100 mulheres"],
)
st.sidebar.caption(f"Fonte: {fonte}")

df = ufs[ufs["regiao"].isin(regioes)].copy()
if df.empty:
    st.warning("Selecione ao menos uma região.")
    st.stop()

# ------------------------------------------------------------------ Título ----
st.title("👩 População feminina no Brasil")
st.caption("Recortes e comparações territoriais — IBGE, Censo Demográfico 2022")

# --------------------------------------------------------------------- KPIs ----
tot_m, tot_h = df["mulheres"].sum(), df["homens"].sum()
pct = tot_m / (tot_m + tot_h) * 100
top = df.loc[df["pct_mulheres"].idxmax()]
low = df.loc[df["pct_mulheres"].idxmin()]
c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi("Mulheres (seleção)", f"{tot_m/1e6:.1f} mi", ROSA, f"{tot_m:,.0f}".replace(",", "."))
with c2:
    kpi("% de mulheres", f"{pct:.2f}%", VERDE, f"{tot_h/tot_m*100:.1f} homens por 100 mulheres")
with c3:
    kpi("Maior proporção", f"{top['sigla']} {top['pct_mulheres']:.1f}%", AZUL, top["uf"])
with c4:
    kpi("Menor proporção", f"{low['sigla']} {low['pct_mulheres']:.1f}%", LARANJA, low["uf"])

st.write("")

# ------------------------------------------------------- Ranking + Rosca ----
col = {"% de mulheres": "pct_mulheres", "Mulheres (absoluto)": "mulheres", "Homens por 100 mulheres": "razao_sexo"}[metrica]
a, b = st.columns([2, 1])
with a:
    r = df.sort_values(col, ascending=False)
    fig = px.bar(r, x="sigla", y=col, color="regiao", hover_name="uf",
                 title=f"Ranking por UF — {metrica}",
                 labels={"sigla": "UF", col: metrica, "regiao": "Região"})
    if col != "mulheres":
        fig.update_yaxes(range=[r[col].min() * 0.98, r[col].max() * 1.01])
    st.plotly_chart(estilo(fig), use_container_width=True)
with b:
    fig = go.Figure(go.Pie(labels=["Mulheres", "Homens"], values=[tot_m, tot_h], hole=0.65,
                           marker_colors=[ROSA, AZUL], textinfo="percent"))
    fig.update_layout(title="Mulheres x Homens (seleção)",
                      annotations=[dict(text=f"<b>{pct:.1f}%</b>", x=0.5, y=0.5, showarrow=False,
                                        font=dict(size=26, color=TXT))])
    st.plotly_chart(estilo(fig), use_container_width=True)

# --------------------------------------------- Região: boxplot + histograma ----
a, b = st.columns(2)
with a:
    fig = px.box(df, x="regiao", y="pct_mulheres", color="regiao", points="all", hover_name="uf",
                 title="Dispersão do % de mulheres por região",
                 labels={"regiao": "", "pct_mulheres": "% de mulheres"})
    fig.update_layout(showlegend=False)
    st.plotly_chart(estilo(fig), use_container_width=True)
with b:
    fig = px.histogram(df, x="pct_mulheres", nbins=10, title="Distribuição do % de mulheres entre as UFs",
                       labels={"pct_mulheres": "% de mulheres"}, color_discrete_sequence=[ROSA])
    fig.add_vline(x=df["pct_mulheres"].mean(), line_dash="dash", line_color=VERDE, annotation_text="média")
    fig.add_vline(x=df["pct_mulheres"].median(), line_dash="dot", line_color=LARANJA, annotation_text="mediana")
    st.plotly_chart(estilo(fig), use_container_width=True)

# --------------------------------------------------- Estatística descritiva ----
st.subheader("📊 Medidas estatísticas — % de mulheres nas UFs")
x = df["pct_mulheres"]
q1, q3 = x.quantile(0.25), x.quantile(0.75)
iqr = q3 - q1
outl = df[(x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)]
moda = x.round(1).mode().iloc[0]
medidas = pd.DataFrame(
    {
        "Medida": ["Média", "Mediana", "Moda (1 casa)", "Q1", "Q3", "IQR", "Amplitude", "Desvio padrão"],
        "Valor (p.p.)": [x.mean(), x.median(), moda, q1, q3, iqr, x.max() - x.min(), x.std()],
    }
).round(3)
a, b = st.columns([1, 2])
with a:
    st.dataframe(medidas, hide_index=True, use_container_width=True)
    if outl.empty:
        st.success("Nenhum outlier pela regra de 1,5 × IQR.")
    else:
        st.warning("Outliers: " + ", ".join(outl["sigla"]))
with b:
    tabela = (
        df.groupby("regiao")
        .agg(mulheres=("mulheres", "sum"), homens=("homens", "sum"),
             media_pct=("pct_mulheres", "mean"), mediana_pct=("pct_mulheres", "median"),
             desvio=("pct_mulheres", "std"))
        .reset_index()
    )
    tabela["% regional"] = tabela["mulheres"] / (tabela["mulheres"] + tabela["homens"]) * 100
    st.dataframe(
        tabela.round(2).rename(columns={"regiao": "Região", "mulheres": "Mulheres", "homens": "Homens",
                                        "media_pct": "Média UFs", "mediana_pct": "Mediana UFs", "desvio": "Desvio"}),
        hide_index=True, use_container_width=True,
    )
st.caption("p.p. = pontos percentuais. Média e mediana próximas indicam distribuição simétrica; "
           "o desvio padrão mostra o quanto as UFs variam entre si.")

# ------------------------------------------------------- Pirâmide etária ----
st.subheader("🔺 Pirâmide etária do Brasil")
pir = carregar_piramide()
if pir is None:
    st.info("Pirâmide indisponível: não foi possível consultar a API do IBGE agora.")
else:
    pir = pir.sort_values("faixa")
    m = pir[pir["sexo"] == "Mulheres"]
    h = pir[pir["sexo"] == "Homens"]
    fig = go.Figure()
    fig.add_bar(y=h["rotulo"], x=-h["valor"], orientation="h", name="Homens", marker_color=AZUL)
    fig.add_bar(y=m["rotulo"], x=m["valor"], orientation="h", name="Mulheres", marker_color=ROSA)
    ticks = np.linspace(-10e6, 10e6, 5)
    fig.update_layout(barmode="overlay", title="População por faixa etária e sexo",
                      xaxis=dict(tickvals=ticks, ticktext=[f"{abs(t)/1e6:.0f} mi" for t in ticks]))
    st.plotly_chart(estilo(fig, 480), use_container_width=True)

# ---------------------------------------------------------------- Tabela ----
st.subheader("📋 Dados por UF")
mostra = df[["uf", "sigla", "regiao", "mulheres", "homens", "pct_mulheres", "razao_sexo"]].sort_values(
    "pct_mulheres", ascending=False
)
mostra.columns = ["UF", "Sigla", "Região", "Mulheres", "Homens", "% mulheres", "Homens/100 mulheres"]
st.dataframe(mostra.round(2), hide_index=True, use_container_width=True)
st.download_button("⬇️ Baixar CSV", mostra.to_csv(index=False).encode("utf-8"), "mulheres_uf.csv", "text/csv")

st.caption("Projeto escolar — Técnico em Informática | Fonte: IBGE (SIDRA), Censo Demográfico 2022.")

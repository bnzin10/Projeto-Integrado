import re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
 
 
AZUL, LARANJA = "#16365c", "#f5a623"
 
st.markdown(f"""
<style>
.stApp {{ background:#e9edf3; }}
[data-testid="stSidebar"] {{ background:{AZUL}; }}
[data-testid="stSidebar"] * {{ color:white !important; }}
.card {{ background:white; color:#1b1b1b; border-radius:6px; padding:18px 20px;
        box-shadow:0 2px 8px rgba(0,0,0,.12); }}
[data-testid="stHeader"] {{ background:transparent; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {{ color: white !important; }}
[data-testid="stMain"] [data-testid="stCaptionContainer"] * {{ color:#3b4350 !important; }}
[data-testid="stMain"] h1, [data-testid="stMain"] [data-testid="stAlert"] * {{ color:#1b1b1b !important; }}
.card.dark, .card.dark * {{ color:white !important; }}
.card.dark {{ background:{AZUL}; color:white; }}
.card .t {{ font-size:14px; opacity:.8; }}
.card .v {{ font-size:34px; font-weight:500; }}
.chart {{ background:white; border-radius:6px; padding:12px;
         box-shadow:0 2px 8px rgba(0,0,0,.12); margin-top:18px; }}
h1 {{ font-size:26px !important; color:#1b1b1b !important; }}
</style>
""", unsafe_allow_html=True)
 
URL = ("https://apisidra.ibge.gov.br/values/t/9606/n1/all/v/93/p/2022"
       "/c86/all/c2/all/c287/all")
 
 
def _midpoint(label):
    m = re.match(r"^(\d+) a (\d+) anos$", label)
    if m and int(m[2]) - int(m[1]) == 4:
        return int(m[1]), int(m[2]) + 1          # [limite inferior, superior)
    m = re.match(r"^(\d+) anos ou mais$", label)
    if m and int(m[1]) == 100:
        return 100, 105
    return None
 
 
@st.cache_data(show_spinner="Consultando o SIDRA/IBGE...")
def carregar_api():
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    dados = r.json()
    cab, linhas = dados[0], pd.DataFrame(dados[1:])
    col = lambda nome: next(k for k, v in cab.items()
                            if k.endswith("N") and nome in v)
    df = pd.DataFrame({
        "raca": linhas[col("Cor")], "sexo": linhas[col("Sexo")],
        "idade": linhas[col("Idade")],
        "pop": pd.to_numeric(linhas["V"], errors="coerce")})
    return df
 
 
def preparar(df):
    df = df[df["sexo"].isin(["Homens", "Mulheres"])].copy()
    df = df[df["raca"] != "Total"]
    lim = df["idade"].map(_midpoint)
    df = df[lim.notna()].copy()
    df["inf"] = lim[lim.notna()].map(lambda x: x[0])
    df["sup"] = lim[lim.notna()].map(lambda x: x[1])
    return df.dropna(subset=["pop"])
 
 
def quantil(g, q):
    """Quantil para dados agrupados em classes (interpolação linear)."""
    g = g.sort_values("inf")
    cum = g["pop"].cumsum()
    alvo = q * g["pop"].sum()
    i = (cum >= alvo).idxmax()
    c = g.loc[i]
    ant = cum.loc[i] - c["pop"]
    return c["inf"] + (alvo - ant) / c["pop"] * (c["sup"] - c["inf"])
 
 
# ---------- Dados ----------
try:
    bruto = carregar_api()
except Exception:
    st.sidebar.warning("Não foi possível acessar a API. Envie um CSV com "
                       "colunas: raca, sexo, idade, pop.")
    up = st.sidebar.file_uploader("CSV", type="csv")
    if up is None:
        st.stop()
    bruto = pd.read_csv(up)
 
df = preparar(bruto)
 
# ---------- Barra lateral ----------
with st.sidebar:
    st.markdown("## 👤 Estudante")
    st.markdown("**População por Grupo de Idade, Sexo e Raça**")
    st.caption("Fonte: IBGE - Censo 2022 (SIDRA, tabela 9606)")
    racas = sorted(df["raca"].unique())
    sel = st.multiselect("Cor ou raça", racas, default=racas)
    sexo = st.radio("Sexo (para as medidas)", ["Ambos", "Homens", "Mulheres"])
 
f = df[df["raca"].isin(sel)]
if f.empty:
    st.warning("Selecione ao menos uma cor ou raça.")
    st.stop()
 
base = f if sexo == "Ambos" else f[f["sexo"] == sexo]
g = (base.groupby(["inf", "sup"], as_index=False)["pop"].sum()
         .sort_values("inf").reset_index(drop=True))
g["mid"] = (g["inf"] + g["sup"]) / 2
 
total = g["pop"].sum()
media = np.average(g["mid"], weights=g["pop"])
dp = np.sqrt(np.average((g["mid"] - media) ** 2, weights=g["pop"]))
q1, med, q3 = (quantil(g, q) for q in (.25, .5, .75))
moda_row = g.loc[g["pop"].idxmax()]
moda = f"{int(moda_row['inf'])} a {int(moda_row['sup'])-1} anos"
amplitude = g["sup"].max() - g["inf"].min()
fem = f[f["sexo"] == "Mulheres"]["pop"].sum()
masc = f[f["sexo"] == "Homens"]["pop"].sum()
razao = f"{masc / fem * 100:.1f}" if fem and masc else "—"
 
# ---------- Cabeçalho e cartões ----------
st.markdown("# Dashboard — Estrutura etária e composição populacional")
 
 
def card(titulo, valor, dark=False):
    return (f'<div class="card {"dark" if dark else ""}"><div class="t">{titulo}'
            f'</div><div class="v">{valor}</div></div>')
 
 
fmt = lambda x: f"{x:,.0f}".replace(",", ".")
c = st.columns(5)
c[0].markdown(card("População total", fmt(total), True), unsafe_allow_html=True)
c[1].markdown(card("Idade média", f"{media:.1f}"), unsafe_allow_html=True)
c[2].markdown(card("Idade mediana", f"{med:.1f}"), unsafe_allow_html=True)
c[3].markdown(card("Desvio padrão", f"{dp:.1f}"), unsafe_allow_html=True)
c[4].markdown(card("Faixa modal", moda), unsafe_allow_html=True)
 
c2 = st.columns(4)
c2[0].markdown(card("Q1 / Q3", f"{q1:.1f} / {q3:.1f}"), unsafe_allow_html=True)
c2[1].markdown(card("IQR", f"{q3 - q1:.1f}"), unsafe_allow_html=True)
c2[2].markdown(card("Amplitude", f"{amplitude:.0f} anos"), unsafe_allow_html=True)
c2[3].markdown(card("Homens por 100 mulheres", razao), unsafe_allow_html=True)
 
# ---------- Gráfico único: pirâmide etária por raça ----------
cores = [AZUL, LARANJA, "#4f8fc0", "#8a9bb0", "#d96c3b", "#2e7d6b"]
rotulos = (f.groupby(["inf", "sup"]).size().reset_index()
             .sort_values("inf"))
faixas = [f"{a} a {b-1}" if a < 100 else "100+" for a, b in
          zip(rotulos["inf"], rotulos["sup"])]
fig = go.Figure()
sexos = ["Homens", "Mulheres"] if sexo == "Ambos" else [sexo]
espelhado = sexo == "Ambos"
for i, r in enumerate(sel):
    for s_ in sexos:
        d = (f[(f["raca"] == r) & (f["sexo"] == s_)]
             .groupby("inf")["pop"].sum().reindex(rotulos["inf"]).fillna(0))
        sinal = -1 if (espelhado and s_ == "Homens") else 1
        fig.add_bar(y=faixas, x=sinal * d.values, orientation="h",
                    name=r, legendgroup=r,
                    showlegend=(s_ == sexos[0]),
                    marker_color=cores[i % len(cores)],
                    opacity=.6 if (espelhado and s_ == "Homens") else 1,
                    customdata=d.values,
                    hovertemplate=f"{r} • {s_}<br>%{{y}} anos<br>"
                                  "%{customdata:,.0f}<extra></extra>")
m = f[f["sexo"].isin(sexos)].groupby(["inf", "sexo"])["pop"].sum().max()
passo = 10 ** int(np.floor(np.log10(m)))
lim = np.ceil(m / passo) * passo
ticks = np.arange(-lim if espelhado else 0, lim + 1, passo)
titulo = {"Ambos": "Pirâmide etária (esq.: homens | dir.: mulheres)",
          "Homens": "População masculina por grupo de idade",
          "Mulheres": "População feminina por grupo de idade"}[sexo]
fig.update_layout(
    template="plotly_white", barmode="relative", height=560, bargap=.08,
    title=titulo + " e cor ou raça",
    font=dict(color="#1b1b1b"),
    xaxis=dict(tickvals=ticks, ticktext=[fmt(abs(t)) for t in ticks]),
    yaxis=dict(title="Grupo de idade (anos)"),
    plot_bgcolor="white", paper_bgcolor="white",
    margin=dict(l=10, r=10, t=50, b=10))
 
st.markdown('<div class="chart">', unsafe_allow_html=True)
st.plotly_chart(fig, width="stretch")
st.markdown('</div>', unsafe_allow_html=True)
st.caption("Medidas calculadas sobre dados agrupados em faixas de 5 anos "
           "(ponto médio da classe; quartis por interpolação linear).")
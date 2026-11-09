import itertools

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROXO, AZUL, LILAS = "#382c5a", "#6f7bc6", "#c9a7e8"
CORES_RACA = {"Branca": "#a0a6dc", "Preta": "#3f51b5", "Parda": "#6f7bc6",
              "Amarela": "#cfd0d8", "Indígena": "#c9a7e8"}
CORES_SEXO = {"Homens": AZUL, "Mulheres": LILAS}

st.markdown(f"""
<style>
.stApp {{background: linear-gradient(135deg,#120826 0%,#1b1038 70%,#0b2a6b 100%);}}
[data-testid="stSidebar"] {{background:{ROXO};}}
[data-testid="stMetric"] {{background:{ROXO};border-radius:18px;padding:14px 18px;text-align:center;}}
[data-testid="stMetricLabel"] {{justify-content:center;}}
h1 {{font-weight:300 !important;}}
h1 b {{font-weight:700;}}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def carregar_dados() -> pd.DataFrame:
    racas = ["Branca", "Preta", "Parda", "Amarela", "Indígena"]
    taxa_raca = dict(zip(racas, [3.3, 7.0, 6.6, 2.0, 14.0]))         
    faixas = ["15-29 anos", "30-59 anos", "60+ anos"]
    mult_faixa = dict(zip(faixas, [0.25, 0.8, 2.6]))
    peso_faixa = dict(zip(faixas, [0.28, 0.48, 0.24]))
    mult_sexo = {"15-29 anos": (1.4, 0.7), "30-59 anos": (1.0, 1.0), "60+ anos": (0.92, 1.07)}
    regioes = ["Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"]
    mult_reg = dict(zip(regioes, [1.1, 1.9, 0.6, 0.55, 0.8]))
    pop_reg = dict(zip(regioes, [13, 43, 70, 24, 13]))                 
    share_raca = {"Norte": [23, 7, 66, 1, 3], "Nordeste": [24, 10, 65, .7, .3],
                  "Sudeste": [50, 10, 38, 1.5, .5], "Sul": [76, 5, 17, 1.5, .5],
                  "Centro-Oeste": [39, 6, 52, 1.5, 2.5]}
    linhas = []
    for ano, reg, (j, raca), faixa, (s, sexo) in itertools.product(
            range(2016, 2025), regioes, enumerate(racas), faixas,
            enumerate(["Homens", "Mulheres"])):
        pop = pop_reg[reg] * share_raca[reg][j] / 100 * peso_faixa[faixa] * (0.51 if s else 0.49)
        taxa = min(0.6, taxa_raca[raca] * mult_faixa[faixa] * mult_sexo[faixa][s]
                   * mult_reg[reg] * np.exp(-0.045 * (ano - 2022)) / 100)
        linhas.append((ano, reg, raca, faixa, sexo, pop, pop * taxa))
    return pd.DataFrame(linhas, columns=["ano", "regiao", "raca", "faixa", "sexo", "populacao", "analf"])


df = carregar_dados()


def taxa_analf(d: pd.DataFrame) -> float:
    return d["analf"].sum() / d["populacao"].sum() if len(d) else np.nan


def layout(fig, h=330):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=h, margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation="h", y=-0.2))
    return fig


st.markdown("# dashboard | alfabetização por <b>sexo e raça</b>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Filtros")
    sexos = st.multiselect("Sexo", ["Homens", "Mulheres"], default=["Homens", "Mulheres"])
    racas_sel = st.multiselect("Cor / Raça", list(CORES_RACA), default=list(CORES_RACA))
    regiao = st.selectbox("Região", ["Brasil"] + sorted(df["regiao"].unique()))
    faixa = st.selectbox("Faixa etária", ["Todas (15+)"] + sorted(df["faixa"].unique()))
    a0, a1 = st.select_slider("Período", options=sorted(df["ano"].unique()), value=(2016, 2024))

sexos = sexos or ["Homens", "Mulheres"]
racas_sel = racas_sel or list(CORES_RACA)

base = df[df["sexo"].isin(sexos)]
if regiao != "Brasil":
    base = base[base["regiao"] == regiao]
if faixa != "Todas (15+)":
    base = base[base["faixa"] == faixa]
base = base[(base["ano"] >= a0) & (base["ano"] <= a1)]
filt = base[base["raca"].isin(racas_sel)]
ult = filt[filt["ano"] == a1]           

ult_base = base[base["ano"] == a1]
t_neg = taxa_analf(ult_base[ult_base["raca"].isin(["Preta", "Parda"])])
t_bra = taxa_analf(ult_base[ult_base["raca"] == "Branca"])
sx = df[(df["ano"] == a1)]
if regiao != "Brasil":
    sx = sx[sx["regiao"] == regiao]
if faixa != "Todas (15+)":
    sx = sx[sx["faixa"] == faixa]
dif_sexo = (taxa_analf(sx[sx["sexo"] == "Mulheres"]) - taxa_analf(sx[sx["sexo"] == "Homens"])) * 100

k1, k2, k3, k4 = st.columns(4)
k1.metric(f"Taxa de alfabetização ({a1})", f"{(1 - taxa_analf(ult)) * 100:.1f}%".replace(".", ","))
k2.metric("Não alfabetizados", f"{ult['analf'].sum():.1f} Mi".replace(".", ","))
k3.metric("Desigualdade racial", f"{t_neg / t_bra:.2f}x".replace(".", ","),
          help="Analfabetismo de pretos+pardos ÷ brancos")
k4.metric("Homens − Mulheres", f"{dif_sexo:+.2f} p.p.".replace(".", ","),
          help="Diferença na taxa de alfabetização")

c_esq, c_dir = st.columns([1, 1.4])

with c_esq:
    st.subheader("Analfabetismo por raça e sexo (%)")
    g = ult.groupby(["raca", "sexo"])[["populacao", "analf"]].sum().reset_index()
    g["taxa"] = g["analf"] / g["populacao"] * 100
    fig = px.bar(g, y="raca", x="taxa", color="sexo", barmode="group", orientation="h",
                 color_discrete_map=CORES_SEXO, text=g["taxa"].round(1),
                 category_orders={"raca": racas_sel})
    fig.update_traces(textposition="outside")
    fig.update_layout(xaxis_title=None, yaxis_title=None, legend_title=None)
    st.plotly_chart(layout(fig), width="stretch")

    st.subheader("Quem são os não alfabetizados")
    d = ult.groupby("raca")["analf"].sum().reset_index()
    fig = px.pie(d, names="raca", values="analf", hole=0.55, color="raca", color_discrete_map=CORES_RACA)
    fig.update_traces(textinfo="label+percent", textposition="outside")
    st.plotly_chart(layout(fig, 300), width="stretch")

with c_dir:
    st.subheader("Evolução da taxa de alfabetização por raça (%)")
    g = filt.groupby(["ano", "raca"])[["populacao", "analf"]].sum().reset_index()
    g["alf"] = (1 - g["analf"] / g["populacao"]) * 100
    fig = px.line(g, x="ano", y="alf", color="raca", markers=True, color_discrete_map=CORES_RACA)
    fig.update_layout(xaxis_title=None, yaxis_title="%", legend_title=None, xaxis=dict(dtick=1))
    st.plotly_chart(layout(fig), width="stretch")

    st.subheader("Hiato racial: pretos+pardos − brancos (p.p. de analfabetismo)")
    gap = []
    for ano, d in base.groupby("ano"):
        gap.append((ano, (taxa_analf(d[d["raca"].isin(["Preta", "Parda"])])
                          - taxa_analf(d[d["raca"] == "Branca"])) * 100))
    gap = pd.DataFrame(gap, columns=["ano", "hiato"])
    fig = go.Figure(go.Scatter(x=gap["ano"], y=gap["hiato"], mode="lines+markers+text",
                               text=gap["hiato"].round(1), textposition="top center",
                               fill="tozeroy", line=dict(color=AZUL),
                               fillcolor="rgba(160,166,220,.35)"))
    fig.update_layout(xaxis=dict(dtick=1), yaxis=dict(rangemode="tozero"))
    st.plotly_chart(layout(fig, 300), width="stretch")

st.info(f"**Leitura:** em {a1}, o analfabetismo entre pretos e pardos é **{t_neg / t_bra:.2f}x** o de brancos "
        f"({regiao}, {faixa.lower()}).".replace(".", ","))
st.caption("⚠ Dados ilustrativos, com ordem de grandeza da PNAD Contínua (IBGE). "
           "Troque `carregar_dados()` por dados reais do IBGE/SIDRA.")

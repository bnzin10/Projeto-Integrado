"""
[Página do painel] Dashboard individual: taxa de desocupação por UF (IBGE, PNAD Contínua, Tabela 4562)
Arquivo único: os dados já estão dentro deste .py (não precisa de Excel nem de upload).
Rodar o painel completo com:  python -m streamlit run painel.py
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.title("Taxa de desocupação por UF")
st.caption("Fonte: IBGE/SIDRA, PNAD Contínua anual, Tabela 4562 (pessoas de 14 anos ou mais, %)")

# ---------- 1. Dados (tabela única embutida) ----------
# colunas: UF, Estado, Região, Ano, Valor (taxa de desocupação em %)
DADOS = [
    ("AC", "Acre", "Norte", 2012, 9.0),
    ("AL", "Alagoas", "Nordeste", 2012, 11.4),
    ("AM", "Amazonas", "Norte", 2012, 9.7),
    ("AP", "Amapá", "Norte", 2012, 13.3),
    ("BA", "Bahia", "Nordeste", 2012, 11.4),
    ("CE", "Ceará", "Nordeste", 2012, 7.8),
    ("DF", "Distrito Federal", "Centro-Oeste", 2012, 8.9),
    ("ES", "Espírito Santo", "Sudeste", 2012, 7.4),
    ("GO", "Goiás", "Centro-Oeste", 2012, 5.0),
    ("MA", "Maranhão", "Nordeste", 2012, 7.9),
    ("MG", "Minas Gerais", "Sudeste", 2012, 6.7),
    ("MS", "Mato Grosso do Sul", "Centro-Oeste", 2012, 6.1),
    ("MT", "Mato Grosso", "Centro-Oeste", 2012, 5.1),
    ("PA", "Pará", "Norte", 2012, 7.3),
    ("PB", "Paraíba", "Nordeste", 2012, 9.6),
    ("PE", "Pernambuco", "Nordeste", 2012, 9.3),
    ("PI", "Piauí", "Nordeste", 2012, 6.0),
    ("PR", "Paraná", "Sul", 2012, 5.0),
    ("RJ", "Rio de Janeiro", "Sudeste", 2012, 7.5),
    ("RN", "Rio Grande do Norte", "Nordeste", 2012, 10.8),
    ("RO", "Rondônia", "Norte", 2012, 5.7),
    ("RR", "Roraima", "Norte", 2012, 7.9),
    ("RS", "Rio Grande do Sul", "Sul", 2012, 5.4),
    ("SC", "Santa Catarina", "Sul", 2012, 3.4),
    ("SE", "Sergipe", "Nordeste", 2012, 10.3),
    ("SP", "São Paulo", "Sudeste", 2012, 7.2),
    ("TO", "Tocantins", "Norte", 2012, 7.9),
    ("AC", "Acre", "Norte", 2022, 12.2),
    ("AL", "Alagoas", "Nordeste", 2022, 12.0),
    ("AM", "Amazonas", "Norte", 2022, 13.1),
    ("AP", "Amapá", "Norte", 2022, 13.7),
    ("BA", "Bahia", "Nordeste", 2022, 15.0),
    ("CE", "Ceará", "Nordeste", 2022, 9.5),
    ("DF", "Distrito Federal", "Centro-Oeste", 2022, 11.4),
    ("ES", "Espírito Santo", "Sudeste", 2022, 8.6),
    ("GO", "Goiás", "Centro-Oeste", 2022, 7.8),
    ("MA", "Maranhão", "Nordeste", 2022, 11.5),
    ("MG", "Minas Gerais", "Sudeste", 2022, 7.7),
    ("MS", "Mato Grosso do Sul", "Centro-Oeste", 2022, 5.0),
    ("MT", "Mato Grosso", "Centro-Oeste", 2022, 4.0),
    ("PA", "Pará", "Norte", 2022, 9.7),
    ("PB", "Paraíba", "Nordeste", 2022, 12.5),
    ("PE", "Pernambuco", "Nordeste", 2022, 16.0),
    ("PI", "Piauí", "Nordeste", 2022, 10.1),
    ("PR", "Paraná", "Sul", 2022, 6.0),
    ("RJ", "Rio de Janeiro", "Sudeste", 2022, 13.3),
    ("RN", "Rio Grande do Norte", "Nordeste", 2022, 12.0),
    ("RO", "Rondônia", "Norte", 2022, 4.2),
    ("RR", "Roraima", "Norte", 2022, 4.9),
    ("RS", "Rio Grande do Sul", "Sul", 2022, 6.4),
    ("SC", "Santa Catarina", "Sul", 2022, 3.9),
    ("SE", "Sergipe", "Nordeste", 2022, 13.2),
    ("SP", "São Paulo", "Sudeste", 2022, 9.1),
    ("TO", "Tocantins", "Norte", 2022, 7.7),
]
df = pd.DataFrame(DADOS, columns=["UF", "Estado", "Região", "Ano", "Valor"])

# ---------- 2. Filtros ----------
ano = st.sidebar.selectbox("Ano", sorted(df["Ano"].unique(), reverse=True))
regioes = st.sidebar.multiselect("Região", sorted(df["Região"].unique()),
                                 default=sorted(df["Região"].unique()))
base_ano = df[(df["Ano"] == ano) & (df["Região"].isin(regioes))]
estados = st.sidebar.multiselect("UF", sorted(base_ano["Estado"]),
                                 default=sorted(base_ano["Estado"]))
d = base_ano[base_ano["Estado"].isin(estados)].copy()

if len(d) < 4:
    st.warning("Selecione pelo menos 4 UFs para calcular quartis.")
    st.stop()

# ---------- 3. Estatísticas ----------
x = d["Valor"]
media, mediana = x.mean(), x.median()
q1, q3 = x.quantile(0.25), x.quantile(0.75)
iqr = q3 - q1
desvio, amplitude = x.std(ddof=1), x.max() - x.min()
moda = x.round(0).mode().iloc[0]                 # moda por valores arredondados
lim_inf, lim_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
d["Outlier"] = (x < lim_inf) | (x > lim_sup)

c = st.columns(6)
c[0].metric("Média", f"{media:.2f}%")
c[1].metric("Mediana", f"{mediana:.2f}%")
c[2].metric("Moda (arredondada)", f"{moda:.0f}%")
c[3].metric("IQR", f"{iqr:.2f} p.p.")
c[4].metric("Desvio padrão", f"{desvio:.2f} p.p.")
c[5].metric("Amplitude", f"{amplitude:.2f} p.p.")
st.caption(f"Q1 = {q1:.2f}% | Q3 = {q3:.2f}% | Limites de outlier (1,5·IQR): "
           f"{lim_inf:.2f}% a {lim_sup:.2f}%")

# ---------- 4. Gráfico único: ranking com média e mediana ----------
r = d.sort_values("Valor")
cores = np.where(r["Outlier"], "#d62728", "#1f77b4")
fig = go.Figure(go.Bar(
    x=r["Valor"], y=r["Estado"], orientation="h", marker_color=cores,
    hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
))
fig.add_vline(x=media, line_dash="dash", line_color="orange",
              annotation_text=f"Média {media:.1f}%", annotation_position="top")
fig.add_vline(x=mediana, line_dash="dot", line_color="green",
              annotation_text=f"Mediana {mediana:.1f}%", annotation_position="bottom")
fig.update_layout(height=700, xaxis_title="Taxa de desocupação (%)", yaxis_title="",
                  title=f"Ranking da taxa de desocupação por UF, {ano} "
                        "(vermelho = outlier pela regra 1,5·IQR)")
st.plotly_chart(fig, width="stretch")

# ---------- 5. Interpretação ----------
out = r[r["Outlier"]]["Estado"].tolist()
maior, menor = r.iloc[-1], r.iloc[0]
if abs(media - mediana) < 0.3:
    forma = "são muito próximas, sugerindo distribuição aproximadamente simétrica"
elif media > mediana:
    forma = "a média fica acima da mediana, sugerindo assimetria à direita (UFs com taxas altas puxam a média)"
else:
    forma = "a média fica abaixo da mediana, sugerindo assimetria à esquerda"
st.subheader("Interpretação")
st.write(
    f"Em {ano}, a maior taxa é de {maior['Estado']} ({maior['Valor']:.1f}%) e a menor é de "
    f"{menor['Estado']} ({menor['Valor']:.1f}%), uma amplitude de {amplitude:.1f} pontos percentuais. "
    f"Média ({media:.2f}%) e mediana ({mediana:.2f}%): {forma}. "
    f"{'Outliers: ' + ', '.join(out) + '.' if out else 'Não há outliers pela regra 1,5·IQR.'} "
    f"O IQR de {iqr:.2f} p.p. mostra a dispersão da metade central das UFs, e o desvio padrão de "
    f"{desvio:.2f} p.p. indica o quanto as UFs se afastam da média, evidenciando desigualdades regionais."
)
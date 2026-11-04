import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Painel IDH", page_icon="📊", layout="wide")
estadosconsorcio = ["Maranhão", "Pará", "Acre", "Bahia", "Minas Gerais"]


@st.cache_data
def ler_tabela(arquivo):
    tabela = pd.read_csv(arquivo, sep=";", skiprows=1, encoding="latin-1", decimal=",")
    tabela = tabela.dropna(subset=["Sigla"])
    anos = []
    for coluna in tabela.columns:
        if str(coluna).strip().isdigit():
            anos.append(coluna)
    dados = tabela.melt(id_vars=["Sigla", "Estado"], value_vars=anos, var_name="Ano", value_name="IDH")
    dados["Ano"] = dados["Ano"].astype(int)
    dados["Sigla"] = dados["Sigla"].str.strip()
    dados["Estado"] = dados["Estado"].str.strip()
    return dados


def faixa_idh(valor):
    if valor >= 0.8:
        return "Muito alto"
    elif valor >= 0.7:
        return "Alto"
    elif valor >= 0.6:  
        return "Médio"
    elif valor >= 0.5:
        return "Baixo"
    else:
        return "Muito baixo"
    

st.sidebar.title("Filtragem")

componente = st.sidebar.selectbox("Componente do IDH", ["Geral", "Longevidade", "Educação", "Renda"])
dados = ler_tabela("Tabela4.csv")

lista_estados = sorted(dados["Estado"].unique())
padrao = []
for estado in estadosconsorcio:
    if estado in lista_estados:
        padrao.append(estado)

estados_escolhidos = st.sidebar.multiselect("Estados (UF)", lista_estados, default=padrao)

listaanos = sorted(dados["Ano"].unique())
ano_comeco = 2000 if 2000 in listaanos else listaanos[0]
ano_inicio, ano_fim = st.sidebar.select_slider(
    "Período", options=listaanos, value=(ano_comeco, listaanos[-1])
)

st.sidebar.markdown("------------------------------------------------------------")
st.sidebar.caption("Análise de dados para o consórcio de governadores")

st.title("Painel do IDH dos Estados")
st.write(
    "Painel feito para o consórcio de governadores que quer criar um fundo regional para reduzir "
    "desigualdades. Aqui dá para acompanhar a evolução do IDH, comparar os estados e ver onde "
    "o investimento social é mais urgente.")

with st.expander("Sobre o projeto e o IDH"):
    st.markdown(
        """
**Quem vai usar o painel:** João (Governador do Maranhão), Helder (Governador do Pará),
Gladson (Governador do Acre), Susu (Governador da Bahia) e Verinha (Governadora de Minas Gerais).

**O que é o IDH:** é o Índice de Desenvolvimento Humano Municipal. Ele junta três dimensões:
**Longevidade** (saúde), **Educação** e **Renda**. Vai de 0 a 1, e quanto mais perto de 1, melhor.

| Faixa | Valor |
|---|---|
| Muito baixo | 0 a 0,499 |
| Baixo | 0,500 a 0,599 |
| Médio | 0,600 a 0,699 |
| Alto | 0,700 a 0,799 |
| Muito alto | 0,800 a 1 |
"""
    )
    
if len(estados_escolhidos) == 0:
    st.warning("Escolha pelo menos um estado na barra lateral.")
    st.stop()

if ano_inicio == ano_fim:
    st.warning("Escolha um período com pelo menos dois anos diferentes.")
    st.stop()

periodo = dados[(dados["Ano"] >= ano_inicio) & (dados["Ano"] <= ano_fim)]
filtrado = periodo[periodo["Estado"].isin(estados_escolhidos)]
final = filtrado[filtrado["Ano"] == ano_fim]
inicio = filtrado[filtrado["Ano"] == ano_inicio]
todos_final = dados[dados["Ano"] == ano_fim]

media_grupo = final["IDH"].mean()
media_grupo_inicio = inicio["IDH"].mean()
media_brasil = todos_final["IDH"].mean()
maior = final.sort_values("IDH", ascending=False).iloc[0]
menor = final.sort_values("IDH").iloc[0]

st.subheader(f"Resumo de {ano_fim} - IDH {componente}")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Média dos escolhidos", f"{media_grupo:.3f}", f"{media_grupo - media_grupo_inicio:+.3f} desde {ano_inicio}")
c2.metric("Média das 27 UFs", f"{media_brasil:.3f}")
c3.metric("Maior IDH", f"{maior['Sigla']} - {maior['IDH']:.3f}")
c4.metric("Menor IDH", f"{menor['Sigla']} - {menor['IDH']:.3f}")
c5.metric("Faixa do grupo", faixa_idh(media_grupo))

aba1, aba2, aba3, aba4, aba5 = st.tabs(
    ["Evolução", "Comparação", "Dispersão", "Prioridades", "Notícias"]
)

with aba1:
    st.subheader(f"Evolução do IDH de {ano_inicio} a {ano_fim}")

    media_por_ano = periodo.groupby("Ano")["IDH"].mean().reset_index()
    media_por_ano["Estado"] = "Média das 27 UFs"
    linhas = pd.concat([filtrado[["Ano", "Estado", "IDH"]], media_por_ano])

    grafico_linha = px.line(linhas, x="Ano", y="IDH", color="Estado", markers=True)
    grafico_linha.update_layout(yaxis_title="IDH", xaxis_title="Ano")
    st.plotly_chart(grafico_linha)

    st.write("**Quanto cada estado cresceu no período**")
    crescimento = inicio[["Estado", "IDH"]].rename(columns={"IDH": f"IDH {ano_inicio}"})
    crescimento = crescimento.merge(
        final[["Estado", "IDH"]].rename(columns={"IDH": f"IDH {ano_fim}"}), on="Estado"
    )
    crescimento["Crescimento"] = crescimento[f"IDH {ano_fim}"] - crescimento[f"IDH {ano_inicio}"]
    crescimento["Crescimento (%)"] = crescimento["Crescimento"] / crescimento[f"IDH {ano_inicio}"] * 100
    crescimento["Faixa atual"] = crescimento[f"IDH {ano_fim}"].apply(faixa_idh)
    crescimento = crescimento.sort_values("Crescimento", ascending=False).round(3)
    st.dataframe(crescimento, hide_index=True)
    
    if 2019 in listaanos and 2021 in listaanos:
        st.write("**Efeito da pandemia: variação do IDH entre 2019 e 2021**")
        antes = dados[(dados["Ano"] == 2019) & (dados["Estado"].isin(estados_escolhidos))][["Estado", "IDH"]]
        depois = dados[(dados["Ano"] == 2021) & (dados["Estado"].isin(estados_escolhidos))][["Estado", "IDH"]]
        pandemia = antes.merge(depois, on="Estado", suffixes=(" 2019", " 2021"))
        pandemia["Variação"] = pandemia["IDH 2021"] - pandemia["IDH 2019"]
        pandemia = pandemia.sort_values("Variação")
        grafico_pandemia = px.bar(pandemia, x="Estado", y="Variação", text_auto=".3f", color="Estado")
        grafico_pandemia.update_layout(showlegend=False, yaxis_title="Variação do IDH")
        st.plotly_chart(grafico_pandemia)

with aba2:
    st.subheader("Gráfico de radar dos estados escolhidos")
    st.caption(
        "Cada ponta do radar é um ano. Quanto mais aberta a forma, maior o IDH. "
        "Assim dá para ver quem está mais longe dos outros ao longo do tempo."
    )
    radar = filtrado.copy()
    radar["Ano"] = radar["Ano"].astype(str)
    menor_valor = radar["IDH"].min()
    maior_valor = radar["IDH"].max()
    grafico_radar = px.line_polar(
        radar, r="IDH", theta="Ano", color="Estado", line_close=True,
        range_r=[round(menor_valor - 0.05, 2), round(maior_valor + 0.02, 2)]
    )
    grafico_radar.update_traces(fill="toself", opacity=0.6)
    st.plotly_chart(grafico_radar)

    st.subheader(f"Ranking das 27 UFs em {ano_fim}")
    ranking = todos_final.sort_values("IDH", ascending=True).copy()
    ranking["Grupo"] = "Outros estados"
    ranking.loc[ranking["Estado"].isin(estados_escolhidos), "Grupo"] = "Estados escolhidos"
    grafico_ranking = px.bar(
        ranking, x="IDH", y="Estado", orientation="h", color="Grupo", text_auto=".3f",
        color_discrete_map={"Estados escolhidos": "#e4572e", "Outros estados": "#a8b3c4"}
    )
    grafico_ranking.update_layout(
        height=750, yaxis_title="",
        xaxis_range=[ranking["IDH"].min() - 0.05, ranking["IDH"].max() + 0.05]
    )
    grafico_ranking.add_vline(x=media_brasil, line_dash="dash", annotation_text="Média das UFs")
    st.plotly_chart(grafico_ranking)

with aba3:
    st.subheader("Ponto de partida x crescimento")
    st.caption(
        f"Cada bolinha é um estado. No eixo X fica o IDH de {ano_inicio} e no eixo Y quanto ele cresceu até {ano_fim}."
    )
    partida = dados[dados["Ano"] == ano_inicio][["Sigla", "Estado", "IDH"]].rename(columns={"IDH": "IDH inicial"})
    chegada = dados[dados["Ano"] == ano_fim][["Estado", "IDH"]].rename(columns={"IDH": "IDH final"})
    dispersao = partida.merge(chegada, on="Estado")
    dispersao["Crescimento"] = dispersao["IDH final"] - dispersao["IDH inicial"]
    dispersao["Grupo"] = "Outros estados"
    dispersao.loc[dispersao["Estado"].isin(estados_escolhidos), "Grupo"] = "Estados escolhidos"

    correlacao = dispersao["IDH inicial"].corr(dispersao["Crescimento"])
    grafico_dispersao = px.scatter(
        dispersao, x="IDH inicial", y="Crescimento", text="Sigla", color="Grupo",
        hover_name="Estado", size="IDH final",
        color_discrete_map={"Estados escolhidos": "#e4572e", "Outros estados": "#a8b3c4"}
    )
    grafico_dispersao.update_traces(textposition="top center")
    st.plotly_chart(grafico_dispersao)
    
    col_a, col_b = st.columns([1, 3])
    col_a.metric("Correlação", f"{correlacao:.2f}")
    if correlacao < -0.3:
        col_b.write(
            "A correlação é **negativa**: os estados que começaram com IDH mais baixo foram os que mais cresceram. "
            "Isso mostra que a diferença entre os estados está diminuindo."
        )
    elif correlacao > 0.3:
        col_b.write(
            "A correlação é **positiva**: os estados que já eram mais desenvolvidos cresceram mais. "
            "Isso mostra que a diferença entre os estados está aumentando."
        )
    else:
        col_b.write("A correlação é **fraca**: o ponto de partida quase não explica o crescimento.")

    st.subheader("Dispersão do IDH entre os estados")
    escolha = st.radio("Comparar entre:", ["Todas as 27 UFs", "Só os estados escolhidos"], horizontal=True)
    if escolha == "Todas as 27 UFs":
        base = periodo
    else:
        base = filtrado

    grafico_caixa = px.box(base, x="Ano", y="IDH", points="all", hover_name="Estado")
    st.plotly_chart(grafico_caixa)
    
    resumo = []
    for ano in sorted(base["Ano"].unique()):
        valores = base[base["Ano"] == ano]["IDH"]
        q1 = valores.quantile(0.25)
        q3 = valores.quantile(0.75)
        resumo.append({
            "Ano": ano,
            "Média": valores.mean(),
            "Mediana": valores.median(),
            "Desvio padrão": valores.std(),
            "Q1": q1,
            "Q3": q3,
            "IQR": q3 - q1,
            "Menor": valores.min(),
            "Maior": valores.max(),
        })
    resumo = pd.DataFrame(resumo).round(3)
    st.dataframe(resumo, hide_index=True)

    grafico_desvio = px.line(resumo, x="Ano", y=["Desvio padrão", "IQR"], markers=True)
    grafico_desvio.update_layout(yaxis_title="Valor", legend_title="Medida")
    st.plotly_chart(grafico_desvio)
    st.caption("Se as linhas caem com o tempo, os estados estão ficando mais parecidos entre si.")

with aba4:
    st.subheader(f"Onde investir primeiro ({ano_fim})")
    prioridade = todos_final[["Sigla", "Estado", "IDH"]].copy()
    prioridade["Posição"] = prioridade["IDH"].rank(ascending=False, method="min").astype(int)
    prioridade = prioridade[prioridade["Estado"].isin(estados_escolhidos)]
    prioridade["Faixa"] = prioridade["IDH"].apply(faixa_idh)
    prioridade["Diferença p/ média"] = prioridade["IDH"] - media_brasil
    prioridade = prioridade.sort_values("IDH").round(3)
    st.dataframe(prioridade, hide_index=True)

    abaixo = prioridade[prioridade["Diferença p/ média"] < 0]
    if len(abaixo) > 0:
        nomes = ", ".join(abaixo["Estado"].tolist())
        st.error(f"Estados abaixo da média das UFs: **{nomes}**. Eles devem ser a prioridade do fundo regional.")
    else:
        st.success("Todos os estados escolhidos estão acima da média das UFs.")

    grafico_distancia = px.bar(
        prioridade, x="Estado", y="Diferença p/ média", color="Faixa", text_auto=".3f"
    )
    grafico_distancia.add_hline(y=0, line_color="black")
    grafico_distancia.update_layout(yaxis_title="Distância da média das UFs")
    st.plotly_chart(grafico_distancia)

    if componente == "Geral":
        st.info(
            "A Tabela 4.1 traz o IDH Geral. Para descobrir qual dimensão (Longevidade, Educação ou Renda) "
            "puxa a nota para baixo, escolha o componente na barra lateral e envie a tabela dele."
        )

with aba5:
    st.subheader("Infográfico: quantas UFs estão em cada faixa")
    faixas = dados.copy()
    faixas["Faixa"] = faixas["IDH"].apply(faixa_idh)
    contagem = faixas.groupby(["Ano", "Faixa"]).size().reset_index(name="Quantidade de UFs")
    contagem["Ano"] = contagem["Ano"].astype(str)
    grafico_faixas = px.bar(
        contagem, x="Ano", y="Quantidade de UFs", color="Faixa",
        category_orders={"Faixa": ["Muito baixo", "Baixo", "Médio", "Alto", "Muito alto"]},
        color_discrete_map={
            "Muito baixo": "#d7191c", "Baixo": "#fdae61", "Médio": "#ffd966",
            "Alto": "#a6d96a", "Muito alto": "#1a9641"
        }
    )
    st.plotly_chart(grafico_faixas)
    
    
st.subheader("Notícias")
noticias = [
        {
            "titulo": "Nordeste lidera maiores avanços estaduais no IDH entre 2012 e 2024",
            "resumo": "Os estados do Nordeste foram os que mais melhoraram o IDH no período e diminuíram a distância para o resto do país.",
            "link": "https://www.undp.org/pt/brazil/news/nordeste-lidera-maiores-avancos-estaduais-no-idhm-entre-2012-e-2024",
        },
        {
            "titulo": "Brasil alcança maior índice de desenvolvimento humano da história",
            "resumo": "Segundo o Radar IDH, o país chegou a 0,805 em 2024 e entrou pela primeira vez na faixa de desenvolvimento muito alto.",
            "link": "https://forbes.com.br/geral/2026/05/brasil-alcanca-maior-indice-de-desenvolvimento-humano-da-historia/",
        },
        {
            "titulo": "Maranhão avança no IDH e entra na faixa de alto desenvolvimento humano",
            "resumo": "O Maranhão chegou a 0,745 em 2024, com crescimento de mais de 6% em três anos.",
            "link": "https://oimparcial.com.br/brasil/2026/05/maranhao-avanca-no-idhm-e-entra-na-faixa-de-alto-desenvolvimento-humano-em-2024/",
        },
        {
            "titulo": "Minas Gerais atinge nível de muito alto desenvolvimento humano",
            "resumo": "Minas chegou a 0,809 em 2024 e passou para a faixa mais alta do índice.",
            "link": "https://diariodocomercio.com.br/economia/idhm-minas-gerais-2024/",
        },
        {
            "titulo": "Brasil voltou a sair do Mapa da Fome",
            "resumo": "Menos de 2,5% da população passou a sofrer de subnutrição, critério usado pela ONU para tirar um país do Mapa da Fome.",
            "link": "https://www.fao.org/brasil/news/detail/Brasil-voltou-a-sair-do-Mapa-da-Fome",
        },  
        {
            "titulo": "Nível de pobreza no Brasil é o menor desde 2012, diz IBGE",
            "resumo": "A extrema pobreza caiu de 4,4% para 3,5% da população em 2024, o menor valor já registrado pelo IBGE.",
            "link": "https://diariodonordeste.verdesmares.com.br/negocios/nivel-de-pobreza-no-brasil-tem-o-menor-nivel-desde-2012-diz-ibge-1.3715380",
        },
        {
            "titulo": "Pandemia causa retrocesso no IDH em todo o país",
            "resumo": "O IDH caiu em todos os estados entre 2020 e 2021, e os programas de transferência de renda ajudaram a segurar a queda.",
            "link": "https://congressoemfoco.com.br/area/pais/pandemia-causa-retrocesso-no-idhm-em-todo-o-pais",
        },
    ]


colunas = st.columns(1)
for i, noticia in enumerate(noticias):
        with colunas[i % 1]:
            with st.container(border=True):
                st.markdown(f"**{noticia['titulo']}**")
                st.write(noticia["resumo"])
                st.link_button("Ler reportagem", noticia["link"])

st.markdown("------------------------------------------------------------")
st.caption(f"Fonte dos dados: Tabela 4.1 - IDH (Índice de Desenvolvimento Humano).")


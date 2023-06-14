"""
2.Pacotes e bibliotecas

pip install geopy
pip install geopandas
pip install geobr
pip install descartes #Usado para resolver um erro ao plotar o mapa.
"""

import pandas as pd
import requests
import seaborn as sns
import geopandas as gpd
import geobr
import matplotlib.pyplot as plt

"""
3.Extração e leitura dos dados
"""

url = 'https://raw.githubusercontent.com/andre-marcos-perez/ebac-course-utils/main/dataset/deliveries.json' #Adicionando o link à variável
filename = 'deliveries.json' #Atribuindo o nome do arquivo à variável
response = requests.get(url) #Adicionando o requests à uma variável
with open(filename, 'wb') as fp: #Criando o arquivo
    fp.write(response.content)

url = 'https://raw.githubusercontent.com/andre-marcos-perez/ebac-course-utils/main/dataset/deliveries-geodata.csv'
filename = 'deliveries-geodata.csv'
response = requests.get(url)
with open(filename, 'wb') as fp:
    fp.write(response.content)

info_bases = pd.read_json("deliveries.json") #Lendo o arquivo e o adicionando à um dataframe

info_entregas = pd.read_csv("deliveries-geodata.csv", header = 0) #Lendo o arquivo e o adicionando à um dataframe e dizendo ao pandas que a linha 0 vai ser o cabeçalho

"""
4.Análise da situação inicial dos dados
"""

info_bases.head() #Analisando as 5 primeiras linhas do dataframe

info_entregas.head()

info_bases.dtypes #Analisando o tipo dos dados do dataframe

info_entregas.dtypes

info_entregas.info() #Analisando dados nulos ou vazios

info_bases.info()

"""
5.Manipulação das colunas que estão como dicionario
"""

info_bases = pd.merge(left=info_bases, right=info_entregas, how="inner", left_index=True, right_index=True) #Fazendo a junção dos dois dataframes usando merge
info_bases.head() #Visualizando

"""
Note que a coluna origin está como dicionário, então usaremos a função json_normalize para separar por colunas, o nome das colunas vai ser a chave de cada dado no dic
"""

info_bases.info()

info_bases_normalized= pd.json_normalize(info_bases["origin"]) #Usando o json_normalize

info_bases_normalized.head() #Analisando como ficaram os dados no dataframe

info_bases = pd.merge(left=info_bases, right=info_bases_normalized, how="inner", left_index=True, right_index=True) #Fazendo a junção dos dataframes usando merge
info_bases.head() #Analisando como ficaram os dados
info_bases.info()

info_bases = info_bases.drop(["origin", "delivery_lat", "delivery_lng"], axis=1) #Removendo as colunas originais e deixando apenas as modificadas
info_bases = info_bases.rename(columns={
"name":"Nome",
"region": "Base",
"vehicle_capacity":"Capacidade_Veiculo",
"deliveries":"Entregas",
"lng":"lng_base",
"lat":"lat_base",
"delivery_city": "Cidade_entrega",
"delivery_suburb":"Região_entrega"
}) #Renomeando cada coluna para minha organização

info_bases = info_bases[["Nome", "Base", "lng_base", "lat_base", "Cidade_entrega", "Região_entrega","Capacidade_Veiculo", "Entregas"]] #Reordenando as colunas para minha organização

info_bases.head() #Analisando o dataframe

"""
Note que a coluna Entregas está como dicionário aninhado, então usaremos a função explode para separa-la em dics
"""

bases_exploded = info_bases[["Entregas"]].explode("Entregas") #Usando a função explode para separas o dic aninhado
bases_exploded.head() #Visualisando

bases_exploded = pd.concat([
    pd.DataFrame(bases_exploded["Entregas"].apply(lambda extrair: extrair["size"])).rename(columns={"Entregas":"Tamanho_Entrega"}),
    pd.DataFrame(bases_exploded["Entregas"].apply(lambda extrair: extrair["point"]["lng"])).rename(columns={"Entregas":"lng_entrega"}),
    pd.DataFrame(bases_exploded["Entregas"].apply(lambda extrair: extrair["point"]["lat"])).rename(columns={"Entregas":"lat_entrega"}),
],axis=1) #Concatenando as colunas a partir das chaves dos dics

bases_exploded.head() #Visualizando

info_bases = info_bases.drop("Entregas", axis=1) #Removendo a coluna original
info_bases = pd.merge(left=info_bases, right=bases_exploded, how="right", left_index=True, right_index=True) #Fazendo a junção dos dataframes usando merge
info_bases.reset_index(inplace=True, drop=True) #Redefinindo os índices
info_bases.head() #Visualizando

"""
6.Manipulação dos dados nulos ou vazios
"""

info_bases.info() #Visualizando

"""
Note que à alguns valores nulos nas colunas Cidade_entrega e Região_entrega, então usarei o fillna para altera-las para Indisponível
"""

info_bases[["Cidade_entrega", "Região_entrega"]] = info_bases[["Cidade_entrega", "Região_entrega"]].fillna("Indisponível") #Usando o fillna para alterar e renomear as colunas nulas

info_bases.info() #Visualizando

"""
 Análise dos dados limpos

6.Plot e resumo de dados para usar nos gráficos
"""

mapa_distrito = geobr.read_municipality(code_muni='DF', year=2020) #Fazendo o plot do gráfico

geo_base = info_bases[["Base", "lng_base", "lat_base"]].drop_duplicates().reset_index(drop= True) #Criando um dataframe para as bases no gráfico, com apenas as lat, lng e nome de cada base individualmente
geo_base_df = gpd.GeoDataFrame( geo_base, geometry=gpd.points_from_xy( geo_base["lng_base"], geo_base["lat_base"] ) )  #Usando a função GeoDataFrame para criar um geodataframe com as coordenadas geográficas dos pontos usando lng_base e lat_base
geo_base_df.info() #Visualizando

geo_entregas_df = gpd.GeoDataFrame( info_bases, geometry=gpd.points_from_xy( info_bases["lng_entrega"], info_bases["lat_entrega"] ) ) #Criando o GeoDataFrame para as entregas
geo_entregas_df.info() #Visualizando

total_entregas = info_bases['Tamanho_Entrega'].sum() #Somando o tamanho das entregas dentro da variável total_entregas

total_entregas_base = info_bases[['Base', 'Tamanho_Entrega']].groupby("Base").agg("sum").reset_index() #Selecionando e agrupando as colunas selecionadas com base na coluna Base
total_entregas_base ['porcentagem_total_entregas'] = round(total_entregas_base ['Tamanho_Entrega'] / total_entregas, 2) #Calculando a porcentagem de cada valor na coluna arredondando para duas casas decimais
total_entregas_base.rename(columns={'Tamanho_Entrega':'total_base', "Base":"região"}, inplace=True) #Renomeando as colunas
total_entregas_base #Visualizando

rank_cidades_entregas = info_bases["Cidade_entrega"].value_counts().reset_index() #Contando a quantidade de entregas em cada cidade
rank_cidades_entregas.rename(columns={"index":"cidade", "Cidade_entrega": "qtd_entregas"}, inplace=True) #Renomeando
rank_cidades_entregas.head() #Visualizando

fig, ax = plt.subplots(figsize = (30/2.54, 30/2.54)) #Criando eixos e tamanho do gráfico
mapa_distrito.plot(ax=ax, alpha= 0.4, color= "lightgrey") #Fazendo o plot do gráfico

"""
6.Gráficos
"""

grafico_1, ax = plt.subplots(figsize=(40, 10))
mapa_distrito.plot(ax=ax, alpha=0.4, color="lightgrey")
#Adicionando as 3 bases e entregas no gráfico
geo_entregas_df.query("Base == 'df-0'").plot(ax=ax, markersize=1, color="red", label="df-0")
geo_entregas_df.query("Base == 'df-1'").plot(ax=ax, markersize=1, color="blue", label="df-1")
geo_entregas_df.query("Base == 'df-2'").plot(ax=ax, markersize=1, color="seagreen", label="df-2")

geo_base_df.plot( ax=ax, markersize=30, marker="x", color="black", label="hub" ) #Definindo tamanho, legenda e simbolo de marcação no gráfico

plt.title( "Entregas no Distrito Federal por Base", fontdict={"fontsize": 16} ) #Adicionando um título e tamanho
lgnd = plt.legend(prop={"size": 15}, markerscale=5, loc="upper right") #Definindo a posição e tamanho da legenda

grafico_2 = plt.figure(figsize=(10, 5))
total_entregas_grafico = sns.barplot(data=total_entregas_base, x='região', y='total_base', ci='sd', palette='muted') #Definindo o gráfico com base na variável total_entregas_base
total_entregas_grafico.set(title='Gráfico 2 - Soma do volume de entregas por base', xlabel='Bases', ylabel='Quantidade de entregas (em milhares)')

with sns.axes_style("whitegrid"):
  grafico_3 = plt.figure(figsize=(10, 5))
  grafico_tamanho_entregas = sns.boxenplot(x=info_bases["Tamanho_Entrega"]) #Definindo o gráfico com base na variável gráfico_tamanho_entregas
  grafico_tamanho_entregas.set(title="Gráfico 4 - Média e outliers do tamanho das entregas", xlabel="Tamanho das entregas")

grafico_4 = plt.figure(figsize=(13, 7))
grafico_rank_cidades = sns.barplot(data=rank_cidades_entregas, x="qtd_entregas", y="cidade", palette= "plasma") #Definindo o gráfico com base na variável grafico_rank_cidades
grafico_rank_cidades.set(title="Gráfico 6 - Cidades com maiores incidências de entregas", xlabel="Quantidade de entregas (em milhares)", ylabel="Cidades")

"""
7.Insights
"""

grafico_1.show()
"""
1° Insight** - No primeiro gráfico, apenas para uma visualização geral do mapa e concentração das entregas, nota-se que a grande parte das entregas estão proximas às bases e analisa-se 
que na base 0 uma grande parte das entregas se distribuem pelo lado direito do mapa.
"""

grafico_2.show()

"""
2° Insight** - Nesse gráfico analisamos melhor a diferença de entregas de cada base, nota-se que a base 0 tem mais que 60% a menos entregas que as demais, porém isso não é algo 
que automaticamente faça dessa base a menos importante.
Pelo falta de dados mais especificos fico impossibilitado de análisar essa área, porém antes de entender o real motivo para essa base ter menos entragas temos que 
entender outros fatores como, rentabilidade, gastos, a quanto tempo a base foi iniciada e até mesmo o tipo de região em que ela se encontra.
Portanto, é importante considerar varios outros fatores e dados antes de termos algum insight favorável sobre isso.
"""

grafico_3.show()

"""
3° Insight** - Usamos esse gráfico para retirar outliers dos dados e com isso temos uma base da média de tamanho das entregas.
Perante a isso ficamos tranquilos quanto à falta de espaço nos caminhões, pois praticamente todos tem seu espaço de 180 então é possivel tranportar varias entregas de uma só vez
e com isso otimizando tempo.
"""

grafico_4.show()

"""
4° Insight** - Quantidade de entregas por cidade é uma ótima maneira de entender e atualizar as rotas de cada base para uma melhor agilidade nas entregas ou talvez transferir 
uma parte da frota de uma região para outra dependendo da demanda.
"""

"""
Resumo dos insights - Em resumo, com a pouca quantidade de dados que eu tive para analisar fica um pouco difícil tirar muitas soluções e melhorias para a área, porém estive 
pensando em dados úteis para essa análise, como as rotas das entregas e o combustível gasto para as respectivas, isso daria uma noção enorme do que melhorar para otimizar o gasto
e a velocidade das entregas.
Outro dado útil seria o peso da carga, pois não temos medidas especificas nos dados, então pode sim ter uma carga de "10" que tenha um peso muito alto para o 
caminhão suportar levar junto com muitas outras.
E por ultimo um dado para controle da empresa que é útil são os status das entregas  como por exemplo, concluída, em andamento, 10 dias para atraso, atrasada e o rastreio do pacote 
para o cliente, não necessariamente muito preciso mas é sim interessante o cliente ter esse feedback.
"""

"""
# 8.Referências

Informações sobre a Loggi: https://www.loggi.com/conheca-a-loggi/

Informações sobre Know-How: https://pt.wikipedia.org/wiki/Saber-fazer#:~:text=O%20termo%20em%20ingl%C3%AAs%20know,de%20como%20executar%20alguma%20tarefa.

Informações sobre a Loggi: https://pt.wikipedia.org/wiki/Loggi

Documentação SeaBorn: https://seaborn.pydata.org/tutorial/color_palettes.html
"""
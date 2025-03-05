import ipeadatapy as idpy
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# i. O primeiro passo é obter no ipeadata http://www.ipeadata.gov.br/Default.aspx os dados descritos a seguir:
    # Nesse caso, usei o módulo ipeadatapy para obter os dados diretamente do Ipeadata

# Pegando os dados a partir do ano desejado
ipca = idpy.timeseries('PRECOS12_IPCA12', yearGreaterThan= 2010)
desocupacao = idpy.timeseries('PNADC12_TDESOC12', yearGreaterThan= 2011)
expectativa = idpy.timeseries('BM12_IPCAEXP1212', yearGreaterThan= 2011)

# Resetando o índice para acessar a coluna 'DATE'
ipca = ipca.reset_index()
desocupacao = desocupacao.reset_index()
expectativa = expectativa.reset_index()

# Convertendo para DataFrame para filtrar pelo mês
ipca = ipca[ipca['DATE'] >= '2011-11-01']
desocupacao = desocupacao[desocupacao['DATE'] >= '2012-11-01']
expectativa = expectativa[expectativa['DATE'] >= '2012-11-01']

# Faxina nos dfs

# Faxina no df ipca
ipca = ipca.drop(columns=['CODE', 'RAW DATE', 'DAY', 'MONTH', 'YEAR'])
ipca = ipca.rename(columns={'VALUE (-)': 'ipca', 'DATE':'data'})

# Faxina no df desocupacao 
desocupacao = desocupacao.drop(columns=['CODE', 'RAW DATE', 'DAY', 'MONTH', 'YEAR'])
desocupacao = desocupacao.rename(columns={'VALUE ((%))': 'taxa_desocupacao', 'DATE':'data'})

# Faxina no df expectativa 
expectativa = expectativa.drop(columns=['CODE', 'RAW DATE', 'DAY', 'MONTH', 'YEAR'])
expectativa = expectativa.rename(columns={'VALUE ((% a.a.))': 'expectativa_inflacao', 'DATE':'data'})

# Resetando os índices dos dataframes
ipca = ipca.reset_index(drop=True)
desocupacao = desocupacao.reset_index(drop=True)
expectativa = expectativa.reset_index(drop=True)

# ii. De posse dos dados calcule π efetiva usando a fórmula acima.

def retorna_inf_efetiva(df, data_inicio):
    inflacao_efetiva = pd.DataFrame()
    inflacao_efetiva['data'] = df['data']
    inflacao_efetiva['inflacao_efetiva'] = (df['ipca'] / df['ipca'].shift(12) - 1) * 100
    inflacao_efetiva = inflacao_efetiva[inflacao_efetiva['data'] >= data_inicio]  # Filtra os dados a partir da data de início
    return inflacao_efetiva

inf_ef = retorna_inf_efetiva(ipca, data_inicio='2012-11-01')

# iii. Organize os dados para o período de tempo da análise.
inf_ef = inf_ef[inf_ef['data'] <= '2023-12-01']
inf_ef = inf_ef.reset_index(drop=True)

# iv. Use o programa de sua preferência para calcular a inflação como dada pelas três versões da curva de Phillips acima.

# Primeiro, vou calcular a taxa natural de desemprego:

desocupacao = desocupacao[desocupacao['data'] <= '2023-12-01']

tx_natural = desocupacao['taxa_desocupacao'].mean()

# Também vou flitrar a expectativa de inflação para o período de análise
expectativa = expectativa[expectativa['data'] <= '2023-12-01']

# Agora, vou definir três funções para calcular a inflação de acordo com as três versões da curva de Phillips

# Versão puro sangue:
def retorna_puro_sangue(desocupacao, expectativa, tx_natural):
    puro_sangue = pd.DataFrame()
    puro_sangue['data'] = expectativa['data']
    puro_sangue['inflacao_puro_sangue'] = (
        6.460 - 0.124 * expectativa['expectativa_inflacao'] - 0.339 * (desocupacao['taxa_desocupacao'] - tx_natural)
    )
    return puro_sangue

# Versão com expectativas adaptativas:
def retorna_expectativas_adaptativas(inf_ef, desocupacao, tx_natural):
    expectativas_adaptativas = pd.DataFrame()
    expectativas_adaptativas['data'] = inf_ef['data']
    expectativas_adaptativas['inflacao_expectativas_adaptativas'] = (
        0.045 + 0.99 * inf_ef['inflacao_efetiva'] + 0.00323 * (desocupacao['taxa_desocupacao'] - tx_natural)
    )
    return expectativas_adaptativas

# Versão híbrida: 
def retorna_hibrida(expectativa, inf_ef, desocupacao, tx_natural):
    hibrida = pd.DataFrame()
    hibrida['data'] = expectativa['data']
    hibrida['inflacao_hibrida'] = (
        0.0543 - 0.0017 * expectativa['expectativa_inflacao'] + 0.99 * inf_ef['inflacao_efetiva'] + 0.0025 * (desocupacao['taxa_desocupacao'] - tx_natural)
    )
    return hibrida

inf_ps = retorna_puro_sangue(desocupacao, expectativa, tx_natural)

inf_ea = retorna_expectativas_adaptativas(inf_ef, desocupacao, tx_natural)

inf_hibrida = retorna_hibrida(expectativa, inf_ef, desocupacao, tx_natural)

# v. Construa um gráfico com as séries ao longo do tempo.

# Criar um gráfico de linha com as diferentes inflações
grafico = px.line(title='Comparação das Inflações ao Longo do Tempo')

# Adicionar cada linha de inflação
grafico.add_scatter(x=inf_ef['data'], y=inf_ef['inflacao_efetiva'], name='Efetiva')
grafico.add_scatter(x=inf_ps['data'], y=inf_ps['inflacao_puro_sangue'], name='Puro Sangue')
grafico.add_scatter(x=inf_hibrida['data'], y=inf_hibrida['inflacao_hibrida'], name='Híbrida')
grafico.add_scatter(x=inf_ea['data'], y=inf_ea['inflacao_expectativas_adaptativas'], name='Expectativas Adaptativas')

# Customizar o layout
grafico.update_layout(
    xaxis_title='Data',
    yaxis_title='Inflação (%)',
    legend_title='Tipos de Inflação'
)

grafico.show()

# Criar uma figura com subplots
grafico = make_subplots(rows=4, cols=1, 
                          subplot_titles=('Inflação Efetiva', 
                                        'Inflação Puro Sangue', 
                                        'Inflação Híbrida', 
                                        'Inflação Expectativas Adaptativas'))

# Adicionar cada linha de inflação em um subplot separado
grafico.add_trace(
    go.Scatter(x=inf_ef['data'], y=inf_ef['inflacao_efetiva'], name='Efetiva'),
    row=1, col=1
)

grafico.add_trace(
    go.Scatter(x=inf_ps['data'], y=inf_ps['inflacao_puro_sangue'], name='Puro Sangue'),
    row=2, col=1
)

grafico.add_trace(
    go.Scatter(x=inf_hibrida['data'], y=inf_hibrida['inflacao_hibrida'], name='Híbrida'),
    row=3, col=1
)

grafico.add_trace(
    go.Scatter(x=inf_ea['data'], y=inf_ea['inflacao_expectativas_adaptativas'], name='Expectativas Adaptativas'),
    row=4, col=1
)

# Customizar o layout
grafico.update_layout(
    height=1000,  # Altura total da figura
    title_text='Comparação das Inflações ao Longo do Tempo',
    showlegend=True
)

# Atualizar os títulos dos eixos
grafico.update_xaxes(title_text='Data')
grafico.update_yaxes(title_text='Inflação (%)')

grafico.show()
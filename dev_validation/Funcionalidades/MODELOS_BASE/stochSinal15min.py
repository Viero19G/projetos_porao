import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

# Obtendo a data e hora atual sem informações de fuso horário
now = datetime.now().replace(tzinfo=None) 
print(now)
pd.options.mode.chained_assignment = None

ativos = ["PETR4.SA"]
data_inicio = "2024-03-04"
lista_bons_para_compra = []
lista_bons_para_venda = []

for ativo in ativos:
    # Obtendo os dados do ativo
    dados_ativo = yf.download(ativo, start=data_inicio, interval="15m")
    dados_ativo.index = dados_ativo.index.tz_localize(None)
    print(dados_ativo)

    # Calculando os retornos
    dados_ativo['Retornos'] = dados_ativo['Adj Close'].pct_change().dropna()

    # Função para filtrar retornos positivos e negativos
    def filtrando_retorno_positivo(x):
        return x if x > 0 else 0

    def filtrando_retorno_negativo(x):
        return abs(x) if x < 0 else 0

    dados_ativo['RetornosPositivos'] = dados_ativo['Retornos'].apply(filtrando_retorno_positivo)
    dados_ativo['RetornosNegativos'] = dados_ativo['Retornos'].apply(filtrando_retorno_negativo)

    # Calculando médias móveis dos retornos positivos e negativos
    dados_ativo['MediaMovelPositiva'] = dados_ativo['RetornosPositivos'].rolling(window=21).mean()
    dados_ativo['MediaMovelNegativa'] = dados_ativo['RetornosNegativos'].rolling(window=21).mean()

    # Calculando o RSI (Índice de Força Relativa)
    dados_ativo['RSI'] = 100 - 100 / (1 + dados_ativo['MediaMovelPositiva'] / dados_ativo['MediaMovelNegativa'])

    # Calculando as bandas de Bollinger
    periodo = 38
    dados_ativo['SMA'] = dados_ativo['Adj Close'].rolling(window=periodo).mean()
    dados_ativo['DesvioPadrao'] = dados_ativo['Adj Close'].rolling(window=periodo).std()
    dados_ativo['BandaSuperior'] = dados_ativo['SMA'] + 1.9 * dados_ativo['DesvioPadrao']
    dados_ativo['BandaInferior'] = dados_ativo['SMA'] - 0.9 * dados_ativo['DesvioPadrao']

    # Sinalizando COMPRA - VENDA com base nas bandas de Bollinger
    dados_ativo.loc[(dados_ativo['Adj Close'] < dados_ativo['BandaInferior']), 'Sinal'] = 'COMPRA'
    dados_ativo.loc[(dados_ativo['Adj Close'] > dados_ativo['BandaSuperior']), 'Sinal'] = 'VENDA'

    # Calculando médias móveis de 8 e 21 períodos
    dados_ativo['MM8'] = dados_ativo['Adj Close'].rolling(window=9).mean()
    dados_ativo['MM21'] = dados_ativo['Adj Close'].rolling(window=20).mean()

    # Calculando o cruzamento das médias móveis
    dados_ativo['CrossOver'] = ((dados_ativo['MM8'] > dados_ativo['MM21']) & (dados_ativo['MM8'].shift(1) <= dados_ativo['MM21'].shift(1))) | ((dados_ativo['MM8'] < dados_ativo['MM21']) & (dados_ativo['MM8'].shift(1) >= dados_ativo['MM21'].shift(1)))

    # Filtrando os pontos de cruzamento
    cruzamentos = dados_ativo[dados_ativo['CrossOver']]

    # Plotando o gráfico com os sinais de COMPRA e VENDA, bem como as médias móveis e os pontos de cruzamento
    plt.figure(figsize=(12, 6))
    plt.plot(dados_ativo.index, dados_ativo['Adj Close'], label='Preço de Fechamento', color='black')
    plt.plot(dados_ativo.index, dados_ativo['BandaSuperior'], label='Banda Superior', linestyle='-', color='orange')
    plt.plot(dados_ativo.index, dados_ativo['BandaInferior'], label='Banda Inferior', linestyle='-', color='orange')
    plt.scatter(dados_ativo[dados_ativo['Sinal'] == 'COMPRA'].index, dados_ativo[dados_ativo['Sinal'] == 'COMPRA']['Adj Close'], label='Sinal de Compra', color='green', marker='o', s=100)
    plt.scatter(dados_ativo[dados_ativo['Sinal'] == 'VENDA'].index, dados_ativo[dados_ativo['Sinal'] == 'VENDA']['Adj Close'], label='Sinal de Venda', color='red', marker='o', s=100)
    plt.plot(dados_ativo.index, dados_ativo['MM8'], label='MM8', color='blue')
    plt.plot(dados_ativo.index, dados_ativo['MM21'], label='MM21', color='red')
    plt.scatter(cruzamentos.index, cruzamentos['Adj Close'], label='Cruzamento de Médias', color='purple', marker='x', s=100)
    plt.title('Preço de Fechamento e Sinais de Compra/Venda ' + ativo)
    plt.xlabel('Data')
    plt.ylabel('Preço de Fechamento')
    plt.legend()
    
print("Lista de Ativos Bons para Compra:", lista_bons_para_compra)
print("Lista de Ativos Bons para Venda: ", lista_bons_para_venda)

# Definindo o capital inicial e o ativo em posse
capital = 1000  # Valor inicial de mil
ativo_em_posse = 0

# Iterando sobre os dados do ativo para simular as operações de compra e venda
for i in range(1, len(dados_ativo)):
    if dados_ativo['Sinal'].iloc[i] == 'COMPRA':
        # Verificando se há capital disponível para comprar o ativo
        if capital > 0:
            ativo_em_posse += capital / dados_ativo['Close'].iloc[i]
            capital = 0
            print(f"COMPRA: Adquiridos {ativo_em_posse} unidades do ativo a {dados_ativo['Close'].iloc[i]} e {dados_ativo.index[i]}")
    elif dados_ativo['Sinal'].iloc[i] == 'VENDA':
        # Verificando se há ativo em posse para vender
        if ativo_em_posse > 0:
            capital += ativo_em_posse * dados_ativo['Close'].iloc[i]
            ativo_em_posse = 0
            print(f"VENDA: Vendidos todos os ativos a {dados_ativo['Close'].iloc[i]}e {dados_ativo.index[i]}")
            print(capital)
            
# Calculando o lucro final
lucro_final = capital
print("Lucro Final:", lucro_final)
plt.show()

import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

# Obtendo a data e hora atual sem informações de fuso horário
now = datetime.now().replace(tzinfo=None)
print(now)
pd.options.mode.chained_assignment = None

ativos = ["BBDC3.SA"]
data_inicio = "2023-04-17"
lista_bons_para_compra = []
lista_bons_para_venda = []

# Definindo os intervalos de períodos e valores para estocástico
periodos_estocasticos = range(0, 1001, 10)  # Lista de 0 a 1000 em incrementos de 10
valores_estocastico = [1, 100]  # Valores para o estocástico

# Dicionário para armazenar os resultados das operações para cada período estocástico
resultados_operacoes = {}

for periodo_estocastico in periodos_estocasticos:
    for ativo in ativos:
        # Obtendo os dados do ativo
        dados_ativo = yf.download(ativo, start=data_inicio, interval="1h")
        dados_ativo.index = dados_ativo.index.tz_localize(None)

        # Calculando o estocástico
        dados_ativo['Minlow'] = dados_ativo['Low'].rolling(window=periodo_estocastico).min()
        dados_ativo['Maxhigh'] = dados_ativo['High'].rolling(window=periodo_estocastico).max()
        dados_ativo['Estocastico'] = 100 * (dados_ativo['Adj Close'] - dados_ativo['Minlow']) / (
            dados_ativo['Maxhigh'] - dados_ativo['Minlow'])

        ####################################################################################################################
        dados_ativo.loc[dados_ativo['Estocastico'] <= valores_estocastico[0], 'Sinal'] = 'COMPRA'
        dados_ativo.loc[dados_ativo['Estocastico'] >= valores_estocastico[1], 'Sinal'] = 'VENDA'

        ####################################################################################################################

        capital = 1000  # Valor inicial de mil
        ativo_em_posse = 0
        lucro_final = 0

        for i in range(1, len(dados_ativo)):
            if dados_ativo['Sinal'].iloc[i] == 'COMPRA':
                # Verificando se há capital disponível para comprar o ativo
                if capital > 0:
                    ativo_em_posse += capital / dados_ativo['Adj Close'].iloc[i]
                    capital = 0
            elif dados_ativo['Sinal'].iloc[i] == 'VENDA':
                # Verificando se há ativo em posse para vender
                if ativo_em_posse > 0:
                    capital += ativo_em_posse * dados_ativo['Adj Close'].iloc[i]
                    ativo_em_posse = 0

        # Salvando o lucro final para este período estocástico
        resultados_operacoes[periodo_estocastico] = capital

# Plotar o gráfico do lucro em função do período estocástico
plt.figure(figsize=(10, 6))
plt.plot(resultados_operacoes.keys(), resultados_operacoes.values(), marker='o', color='blue')
plt.title('Lucro em função do Período Estocástico')
plt.xlabel('Período Estocástico')
plt.ylabel('Lucro Final')
plt.grid(True)
plt.show()
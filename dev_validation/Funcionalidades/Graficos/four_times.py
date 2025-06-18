import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk

# Função para baixar e processar os dados
def processar_dados(ativo, intervalos):
    dados = {}
    
    for intervalo in intervalos:
        try:
            # Se o intervalo for 15m ou 60m, limitar o período a 60 dias
            if intervalo in ['15m', '60m']:
                df = yf.download(ativo, period='60d', interval=intervalo)
            else:
                df = yf.download(ativo, period='1y', interval=intervalo)
            
            df['MA50'] = df['Close'].rolling(window=3).mean()
            dados[intervalo] = df
        except Exception as e:
            print(f"Erro ao baixar dados para o intervalo {intervalo}: {e}")
    
    return dados

# Função para verificar sinais de compra e venda
def verificar_sinais(dados):
    sinais_compra = []
    sinais_venda = []
    
    try:
        for i in range(1, len(dados['1d'])):
            if (dados['1d']['MA50'].iloc[i] > dados['1d']['MA50'].iloc[i-1] and
                dados['60m']['MA50'].iloc[i] > dados['60m']['MA50'].iloc[i-1] and
                dados['15m']['MA50'].iloc[i] > dados['15m']['MA50'].iloc[i-1]):
                sinais_compra.append(dados['1d'].index[i])
            
            if (dados['1d']['MA50'].iloc[i] < dados['1d']['MA50'].iloc[i-1] and
                dados['60m']['MA50'].iloc[i] < dados['60m']['MA50'].iloc[i-1] and
                dados['15m']['MA50'].iloc[i] < dados['15m']['MA50'].iloc[i-1]):
                sinais_venda.append(dados['1d'].index[i])
    
    except KeyError as e:
        print(f"Erro ao acessar dados para o intervalo: {e}")

    return sinais_compra, sinais_venda

# Função para exibir o gráfico com os sinais de compra e venda
def exibir_grafico(dados, sinais_compra, sinais_venda):
    plt.figure(figsize=(10, 6))

    for intervalo, df in dados.items():
        plt.plot(df.index, df['Close'], label=f"Fechamento ({intervalo})")
        plt.plot(df.index, df['MA50'], label=f"MA50 ({intervalo})")

    for sinal in sinais_compra:
        plt.scatter(sinal, dados['1d'].loc[sinal, 'Close'], color='green', marker='o', label='Compra')

    for sinal in sinais_venda:
        plt.scatter(sinal, dados['1d'].loc[sinal, 'Close'], color='red', marker='o', label='Venda')

    plt.legend()
    plt.show()

# Função principal para rodar a análise
def rodar_analise(ativo, intervalos):
    dados = processar_dados(ativo, intervalos)
    sinais_compra, sinais_venda = verificar_sinais(dados)
    exibir_grafico(dados, sinais_compra, sinais_venda)

# Interface gráfica para seleção dos tempos gráficos
def criar_interface():
    def iniciar():
        ativo = entrada_ativo.get()
        intervalo1 = combo1.get()
        intervalo2 = combo2.get()
        intervalo3 = combo3.get()
        intervalos = [intervalo1, intervalo2, intervalo3]
        
        rodar_analise(ativo, intervalos)

    janela = tk.Tk()
    janela.title("Análise de Ativos")

    tk.Label(janela, text="Selecione o ativo:").pack()
    entrada_ativo = tk.Entry(janela)
    entrada_ativo.pack()

    tk.Label(janela, text="Escolha os três tempos gráficos:").pack()

    intervalos_opcoes = ['1d', '60m', '15m', '1wk', '1mo','5d','3mo','6mo','2m', '5m','90m','1h']

    combo1 = ttk.Combobox(janela, values=intervalos_opcoes)
    combo1.set('1d')
    combo1.pack()

    combo2 = ttk.Combobox(janela, values=intervalos_opcoes)
    combo2.set('60m')
    combo2.pack()

    combo3 = ttk.Combobox(janela, values=intervalos_opcoes)
    combo3.set('15m')
    combo3.pack()

    botao_iniciar = tk.Button(janela, text="Iniciar Análise", command=iniciar)
    botao_iniciar.pack()

    janela.mainloop()

# Executar interface
criar_interface()
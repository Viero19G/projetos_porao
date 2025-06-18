import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import io

# Obtendo a data e hora atual sem informações de fuso horário
now = datetime.now().replace(tzinfo=None)
print(now)
pd.options.mode.chained_assignment = None

# ativos = ['MATIC-USD','ETH-USD','AAVE-USD','LINK-USD']
ativos = ['PETR4.SA','ABEV3.SA','ALOS3.SA','ARZZ3.SA','ASAI3.SA','AZUL4.SA','B3SA3.SA','BBAS3.SA','BBDC3.SA','BBDC4.SA','BBSE3.SA','BEEF3.SA','BHIA3.SA','BOVA11.SA','BPAC11.SA','BRAP4.SA','BRFS3.SA','BRKM5.SA','CCRO3.SA',
'CIEL3.SA', 'CMIG4.SA', 'CMIN3.SA', 'COGN3.SA', 'CPLE6.SA', 'CSAN3.SA', 'CSNA3.SA', 'CVCB3.SA', 'CXSE3.SA', 'CYRE3.SA', 'EGIE3.SA', 'ELET3.SA', 'ELET6.SA', 'EMBR3.SA', 'ENAT3.SA', 'EQTL3.SA', 'FLRY3.SA', 'GFSA3.SA', 'GGBR4.SA', 'GOAU4.SA', 'HAPV3.SA', 'HYPE3.SA', 'IGTI11.SA', 'IRBR3.SA', 'ITSA4.SA', 'ITUB4.SA', 'JBSS3.SA', 'KLBN11.SA', 'LEVE3.SA', 'LREN3.SA', 'LWSA3.SA', 'MGLU3.SA', 'MRFG3.SA', 'MRVE3.SA', 'MULT3.SA', 'NTCO3.SA', 'PCAR3.SA', 'PETR3.SA',
          'PETR4.SA','PETZ3.SA','PRIO3.SA','PSSA3.SA','QUAL3.SA','RADL3.SA','RAIL3.SA','RAIZ4.SA','RDOR3.SA','RENT3.SA','RRRP3.SA','SANB11.SA','SBSP3.SA','SEER3.SA','SMAL11.SA','SOMA3.SA','SUZB3.SA','TAEE11.SA','TIMS3.SA','TOTS3.SA','UGPA3.SA','USIM5.SA','VALE3.SA','VBBR3.SA','WEGE3.SA','YDUQ3.SA']


data_inicio = "2010-03-01"
lista_bons_para_compra = []
lista_bons_para_venda = []

for ativo in ativos:
    # Obtendo os dados do ativo
    dados_ativo = yf.download(ativo, start=data_inicio, interval="1d")
    print(dados_ativo)

    # Calculando os retornos
    dados_ativo['Retornos'] = dados_ativo['Adj Close'].pct_change().dropna()

    # Função para filtrar retornos positivos e negativos
    def filtrando_retorno_positivo(x):
        return x if x > 0 else 0

    def filtrando_retorno_negativo(x):
        return abs(x) if x < 0 else 0

    dados_ativo['RetornosPositivos'] = dados_ativo['Retornos'].apply(
        filtrando_retorno_positivo)
    dados_ativo['RetornosNegativos'] = dados_ativo['Retornos'].apply(
        filtrando_retorno_negativo)

    # Calculando médias móveis dos retornos positivos e negativos
    dados_ativo['MediaMovelPositiva'] = dados_ativo['RetornosPositivos'].rolling(
        window=21).mean()
    dados_ativo['MediaMovelNegativa'] = dados_ativo['RetornosNegativos'].rolling(
        window=21).mean()

    # Calculando o RSI (Índice de Força Relativa)
    dados_ativo['RSI'] = 100 - 100 / \
        (1 + dados_ativo['MediaMovelPositiva'] /
         dados_ativo['MediaMovelNegativa'])

    # Calculando as bandas de Bollinger
    periodo = 38
    dados_ativo['SMA'] = dados_ativo['Adj Close'].rolling(
        window=periodo).mean()
    dados_ativo['DesvioPadrao'] = dados_ativo['Adj Close'].rolling(
        window=periodo).std()
    dados_ativo['BandaSuperior'] = dados_ativo['SMA'] + \
        3.0 * dados_ativo['DesvioPadrao']
    dados_ativo['BandaInferior'] = dados_ativo['SMA'] - \
        0.8 * dados_ativo['DesvioPadrao']

    # Sinalizando COMPRA - VENDA com base nas bandas de Bollinger ####################
    # CONDIÇÃO COMPRA/VENDA
    dados_ativo.loc[(dados_ativo['Adj Close'] <
                     dados_ativo['BandaInferior']), 'Sinal'] = 'COMPRA'
    dados_ativo.loc[(dados_ativo['Adj Close'] >
                     dados_ativo['BandaSuperior']), 'Sinal'] = 'VENDA'

    # Calculando médias móveis de 8 e 21 períodos
    dados_ativo['MM8'] = dados_ativo['Adj Close'].rolling(window=14).mean()
    dados_ativo['MM21'] = dados_ativo['Adj Close'].rolling(window=21).mean()

    # Ordenar os dados por data
    dados_ativo = dados_ativo.sort_index()

  # Converter o índice para um tipo de datetime ingênuo
  # deixar a linha abaixo descomentada apenas para previsões por Hora e minuto
    # dados_ativo.index = dados_ativo.index.tz_convert(None)

# Encontrar o último sinal de COMPRA antes da hora atual
    ultimo_sinal_compra = dados_ativo[dados_ativo.index <
                                      now][dados_ativo['Sinal'] == 'COMPRA'].tail(1)

    # # Verificar se o sinal COMPRA está ativo
    if not dados_ativo.empty and dados_ativo.iloc[-1]['Sinal'] == 'COMPRA':
        # Verificar se o MM8 atual é maior que o MM21 atual
        if dados_ativo.iloc[-1]['MM8'] > dados_ativo.iloc[-1]['MM21']:
            # Verificar se o MM8 e MM21 do momento do sinal são menores que os atuais
            if dados_ativo[dados_ativo['Sinal'] == 'COMPRA'].iloc[0]['MM8'] < dados_ativo.iloc[-1]['MM8'] and \
               dados_ativo[dados_ativo['Sinal'] == 'COMPRA'].iloc[0]['MM21'] < dados_ativo.iloc[-1]['MM21']:
                lista_bons_para_compra.append(ativo)

    if not dados_ativo.empty and dados_ativo.iloc[-1]['Sinal'] == 'VENDA':
        # Verificar se o MM8 atual é maior que o MM21 atual
        if dados_ativo.iloc[-1]['MM8'] < dados_ativo.iloc[-1]['MM21']:
            # Verificar se o MM8 e MM21 do momento do sinal são menores que os atuais
            if dados_ativo[dados_ativo['Sinal'] == 'COMPRA'].iloc[0]['MM8'] > dados_ativo.iloc[-1]['MM8'] and \
               dados_ativo[dados_ativo['Sinal'] == 'COMPRA'].iloc[0]['MM21'] > dados_ativo.iloc[-1]['MM21']:
                lista_bons_para_venda.append(ativo)

    # # Plotando o gráfico com os sinais de COMPRA e VENDA, bem como as médias móveis
    # plt.figure(figsize=(12, 6))
    # plt.plot(dados_ativo.index,
    #          dados_ativo['Adj Close'], label='Preço de Fechamento', color='black')
    # plt.plot(dados_ativo.index, dados_ativo['BandaSuperior'],
    #          label='Banda Superior', linestyle='-', color='orange')
    # plt.plot(dados_ativo.index, dados_ativo['BandaInferior'],
    #          label='Banda Inferior', linestyle='-', color='orange')
    # plt.scatter(dados_ativo[dados_ativo['Sinal'] == 'COMPRA'].index,
    #             dados_ativo[dados_ativo['Sinal'] == 'COMPRA']['Adj Close'],
    #             label='Sinal de Compra', color='green', marker='o', s=100)
    # plt.scatter(dados_ativo[dados_ativo['Sinal'] == 'VENDA'].index,
    #             dados_ativo[dados_ativo['Sinal'] == 'VENDA']['Adj Close'],
    #             label='Sinal de Venda', color='red', marker='o', s=100)
    # plt.plot(dados_ativo.index, dados_ativo['MM8'], label='MM8', color='blue')
    # plt.plot(dados_ativo.index, dados_ativo['MM21'], label='MM21', color='red')
    # plt.title('Preço de Fechamento e Sinais de Compra/Venda ' + ativo)
    # plt.xlabel('Data')
    # plt.ylabel('Preço de Fechamento')
    # plt.legend()
    # plt.show()

print("Lista de Ativos Bons para Compra:", lista_bons_para_compra)
print("Lista de Ativos Bons para Venda: ", lista_bons_para_venda)  


# Enviar e-mail com as listas de ativos bons para compra e venda e os gráficos gerados
email_sender = "gabrielviero22@gmail.com"
email_receiver = "gilneiviero97@gmail.com"
email_password = "yscctdbdocoqaxhk"

# Configurando o servidor SMTP
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(email_sender, email_password)

# Criando o e-mail
msg = MIMEMultipart()
msg['From'] = email_sender
msg['To'] = email_receiver
msg['Subject'] = 'Relatório de Ativos'

# Corpo do e-mail
body = f"""
Lista de Ativos Bons para Compra: {lista_bons_para_compra}
Lista de Ativos Bons para Venda: {lista_bons_para_venda}
"""
msg.attach(MIMEText(body, 'plain'))


# Enviando o e-mail
server.sendmail(email_sender, email_receiver, msg.as_string())
server.quit()

print("E-mail enviado com sucesso!")

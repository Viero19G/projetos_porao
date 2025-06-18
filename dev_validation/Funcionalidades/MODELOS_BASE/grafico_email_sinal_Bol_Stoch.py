import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

pd.options.mode.chained_assignment = None

# ativos = ['ABEV3.SA','ALOS3.SA','ARZZ3.SA','ASAI3.SA','AZUL4.SA','B3SA3.SA','BBAS3.SA','BBDC3.SA','BBDC4.SA','BBSE3.SA','BEEF3.SA','BHIA3.SA','BOVA11.SA','BPAC11.SA','BRAP4.SA','BRFS3.SA','BRKM5.SA','CCRO3.SA',
# 'CIEL3.SA', 'CMIG4.SA', 'CMIN3.SA', 'COGN3.SA', 'CPLE6.SA', 'CSAN3.SA', 'CSNA3.SA', 'CVCB3.SA', 'CXSE3.SA', 'CYRE3.SA', 'EGIE3.SA', 'ELET3.SA', 'ELET6.SA', 'EMBR3.SA', 'ENAT3.SA', 'EQTL3.SA', 'FLRY3.SA', 'GFSA3.SA', 'GGBR4.SA', 'GOAU4.SA', 'HAPV3.SA', 'HYPE3.SA', 'IGTI11.SA', 'IRBR3.SA', 'ITSA4.SA', 'ITUB4.SA', 'JBSS3.SA', 'KLBN11.SA', 'LEVE3.SA', 'LREN3.SA', 'LWSA3.SA', 'MGLU3.SA', 'MRFG3.SA', 'MRVE3.SA', 'MULT3.SA', 'NTCO3.SA', 'PCAR3.SA', 'PETR3.SA',
#           'PETR4.SA','PETZ3.SA','PRIO3.SA','PSSA3.SA','QUAL3.SA','RADL3.SA','RAIL3.SA','RAIZ4.SA','RDOR3.SA','RENT3.SA','RRRP3.SA','SANB11.SA','SBSP3.SA','SEER3.SA','SMAL11.SA','SOMA3.SA','SUZB3.SA','TAEE11.SA','TIMS3.SA','TOTS3.SA','UGPA3.SA','USIM5.SA','VALE3.SA','VBBR3.SA','WEGE3.SA','YDUQ3.SA']
criptos = [
    "MATIC-USD", "ICP1-USD", "XLM-USD",
    "BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "ADA-USD",
    "DOGE-USD", "DOT1-USD", "UNI3-USD", "BCH-USD", "LTC-USD",
    "ETC-USD", "VET-USD", "FIL-USD", "THETA-USD", "TRX-USD",
    "EOS-USD", "AAVE-USD", "XMR-USD", "ATOM1-USD", "NEO-USD",
    "WBTC-USD", "MKR-USD", "XTZ-USD", "FTT-USD", "HT-USD",
    "COMP-USD", "ALGO-USD", "DASH-USD", "SNX-USD", "HNT-USD",
    "GRT-USD", "ENJ-USD", "BAT-USD", "ZEC-USD", "UMA-USD",
    "SUSHI-USD", "MANA-USD", "YFI-USD", "ZRX-USD", "SAND-USD",
    "REN-USD", "OKB-USD", "BTT-USD", "FLOW-USD", "RVN-USD"
]

ativos = list(set(criptos))
data_atual = datetime.now()
data_inicio = data_atual - timedelta(days=700)


bons_para_compra = []
bons_para_venda = []
com_problema = []
for ativo in ativos:
    try:
        # Obtendo os dados do ativo
        dados_ativo = yf.download(ativo, start=data_inicio, interval="1d")
        # print(dados_ativo)
        # print(dados_ativo)
        # Verificando se há dados disponíveis
        if dados_ativo.empty:
            raise ValueError(f"Nenhum dado disponível para {ativo}")

        # Calculando os retornos
        dados_ativo['Retornos'] = dados_ativo['Adj Close'].pct_change().dropna()
        
        # Continue com o processamento dos dados...
    except Exception as e:
        com_problema.append(ativo)
        print(f"Erro ao obter dados para {ativo}: {e}")
        continue

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
        window=14).mean()
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
        0.9 * dados_ativo['DesvioPadrao']
    dados_ativo['BandaInferior'] = dados_ativo['SMA'] - \
        1.9 * dados_ativo['DesvioPadrao']

#####################################################################################################################
################################  DESCOMENTAR PARA COMPRA COM BANDA DE BOLINGER #####################################
    # Sinalizando COMPRA - VENDA com base nas bandas de Bollinger
    dados_ativo.loc[(dados_ativo['Adj Close'] <
                     dados_ativo['BandaInferior']), 'Sinal'] = 'COMPRA'
    dados_ativo.loc[(dados_ativo['Adj Close'] >
                     dados_ativo['BandaSuperior']), 'Sinal'] = 'VENDA'

    ################################################################################################################
    # Ajustando calculos para medidas

    # Calculando o estocástico
    periodo_estocastico = 140
    dados_ativo['MinLow'] = dados_ativo['Low'].rolling(
        window=periodo_estocastico).min()
    dados_ativo['MaxHigh'] = dados_ativo['High'].rolling(
        window=periodo_estocastico).max()
    dados_ativo['Estocastico'] = 100 * (dados_ativo['Adj Close'] - dados_ativo['MinLow']) / (
        dados_ativo['MaxHigh'] - dados_ativo['MinLow'])

    periodo_estocastico_30 = 30
    dados_ativo['MinLow_30'] = dados_ativo['Low'].rolling(
        window=periodo_estocastico_30).min()
    dados_ativo['MaxHigh_30'] = dados_ativo['High'].rolling(
        window=periodo_estocastico_30).max()
    dados_ativo['Estocastico_30'] = 100 * (dados_ativo['Adj Close'] - dados_ativo['MinLow_30']) / (
        dados_ativo['MaxHigh_30'] - dados_ativo['MinLow_30'])

    periodo_estocastico_8 = 8
    dados_ativo['MinLow_8'] = dados_ativo['Low'].rolling(
        window=periodo_estocastico_8).min()
    dados_ativo['MaxHigh_8'] = dados_ativo['High'].rolling(
        window=periodo_estocastico_8).max()
    dados_ativo['Estocastico_8'] = 100 * (dados_ativo['Adj Close'] - dados_ativo['MinLow_8']) / (
        dados_ativo['MaxHigh_8'] - dados_ativo['MinLow_8'])

    ####################################################################################################################
    dados_ativo.loc[(dados_ativo['Estocastico_8'] <= 20) & (dados_ativo['Estocastico_30'] <= 20) & (dados_ativo['Estocastico']  <= 20 ), 'Sinal'] = 'COMPRA'
    
    dados_ativo.loc[(dados_ativo['Estocastico_8'] >= 80) & (dados_ativo['Estocastico_30'] >= 80 ) & (dados_ativo['Estocastico']  >= 80 ), 'Sinal'] = 'VENDA'
    
 
    
    
    
    
    ####################################################################################################################

    # Calculando as médias móveis de 14 e 21 períodos
    dados_ativo['MediaMovel14'] = dados_ativo['Adj Close'].rolling(
        window=21).mean()
    dados_ativo['MediaMovel21'] = dados_ativo['Adj Close'].rolling(
        window=71).mean()

    # Marcando os pontos do estocástico
    dados_ativo.loc[dados_ativo['Estocastico'] <= 20,
                    'Estocastico_20'] = dados_ativo['Adj Close']
    dados_ativo.loc[dados_ativo['Estocastico'] >= 80,
                    'Estocastico_80'] = dados_ativo['Adj Close']

    # Verificar se a data atual está presente nos índices do DataFrame

    ultimo_index = dados_ativo.index[-1].to_pydatetime()
    if ultimo_index in dados_ativo.index:
        print(data_atual)
        # Obtendo o índice correspondente ao último datetime
        indice_agora = dados_ativo.index.get_loc(ultimo_index)
        print(indice_agora)
        # Verificar se há um sinal de COMPRA no índice correspondente ao datetime.now()
        if dados_ativo.iloc[indice_agora]['Sinal'] == 'COMPRA':
            bons_para_compra.append(ativo)
        if dados_ativo.iloc[indice_agora]['Sinal'] == 'VENDA':
            bons_para_venda.append(ativo)
    # # Plotando os gráficos
    fig, axs = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

    # Gráfico 1 - Preço de Fechamento, Médias Móveis, Estocástico <= 20 e >= 80, Sinais de COMPRA e VENDA
    axs[0].plot(dados_ativo.index, dados_ativo['Adj Close'], label='Preço de Fechamento', color='black')
    axs[0].plot(dados_ativo.index, dados_ativo['MediaMovel14'], label='Média Móvel 14', color='blue')
    axs[0].plot(dados_ativo.index, dados_ativo['MediaMovel21'], label='Média Móvel 21', color='red')
    axs[0].scatter(dados_ativo.index, dados_ativo['Estocastico_20'], label='Estocástico <= 20', color='yellow', marker='o', s=100)
    axs[0].scatter(dados_ativo.index, dados_ativo['Estocastico_80'], label='Estocástico >= 80', color='orange', marker='o', s=100)
    axs[0].scatter(dados_ativo[dados_ativo['Sinal'] == 'COMPRA'].index, dados_ativo[dados_ativo['Sinal'] == 'COMPRA']['Adj Close'], label='COMPRA', color='green', marker='^', s=100)
    axs[0].scatter(dados_ativo[dados_ativo['Sinal'] == 'VENDA'].index, dados_ativo[dados_ativo['Sinal'] == 'VENDA']['Adj Close'], label='VENDA', color='red', marker='v', s=100)
    axs[0].plot(dados_ativo.index, dados_ativo['BandaSuperior'], label='Banda Superior', color='purple', linestyle='--')
    axs[0].plot(dados_ativo.index, dados_ativo['BandaInferior'], label='Banda Inferior', color='green', linestyle='--')
    axs[0].title.set_text(f'Preço de Fechamento, Médias Móveis, Estocástico e Sinais para {ativo}')
    axs[0].set_ylabel('Preço de Fechamento')
    axs[0].legend()

    # Gráfico 2 - Estocástico com SMTHK = 1, SMTHD = 30, e Length = 14

    ##### Ajustar janela(window)
    axs[1].plot(dados_ativo.index, dados_ativo['Estocastico'], label='Estocástico', color='black')
    axs[1].plot(dados_ativo.index, dados_ativo['Estocastico'].rolling(window=1).mean(), label='SMTHK = 1', color='blue')
    axs[1].plot(dados_ativo.index, dados_ativo['Estocastico'].rolling(window=3).mean(), label='SMTHD = 3', color='red')
    axs[1].axhline(y=20, color='gray', linestyle='--')
    axs[1].axhline(y=80, color='gray', linestyle='--')
    axs[1].title.set_text('Estocástico com SMTHK = 1, SMTHD = 3, e Length = 140')
    axs[1].set_xlabel('Data')
    axs[1].set_ylabel('Estocástico')
    axs[1].legend()

    axs[2].plot(dados_ativo.index, dados_ativo['Estocastico_30'], label='Estocástico_30', color='black')
    axs[2].plot(dados_ativo.index, dados_ativo['Estocastico_30'].rolling(window=1).mean(), label='SMTHK = 1', color='blue')
    axs[2].plot(dados_ativo.index, dados_ativo['Estocastico_30'].rolling(window=3).mean(), label='SMTHD = 3', color='red')
    axs[2].axhline(y=20, color='gray', linestyle='--')
    axs[2].axhline(y=80, color='gray', linestyle='--')
    axs[2].title.set_text('Estocástico com SMTHK = 1, SMTHD = 3, e Length = 30')
    axs[2].set_xlabel('Data')
    axs[2].set_ylabel('Estocástico_30')
    axs[2].legend()

    axs[3].plot(dados_ativo.index, dados_ativo['Estocastico_8'], label='Estocástico_8', color='black')
    axs[3].plot(dados_ativo.index, dados_ativo['Estocastico_8'].rolling(window=1).mean(), label='SMTHK = 1', color='blue')
    axs[3].plot(dados_ativo.index, dados_ativo['Estocastico_8'].rolling(window=3).mean(), label='SMTHD = 3', color='red')
    axs[3].axhline(y=20, color='gray', linestyle='--')
    axs[3].axhline(y=80, color='gray', linestyle='--')
    axs[3].title.set_text('Estocástico com SMTHK = 1, SMTHD = 3, e Length = 8')
    axs[3].set_xlabel('Data')
    axs[3].set_ylabel('Estocástico_8')
    axs[3].legend()

    plt.tight_layout()
    # plt.show()
# Configuração do email
# email_sender = "gabrielviero22@gmail.com"
# email_receiver = "gilneiviero97@gmail.com"
# email_password = "yscctdbdocoqaxhk"

# # Configurando o servidor SMTP
# server = smtplib.SMTP('smtp.gmail.com', 587)
# server.starttls()
# server.login(email_sender, email_password)    


print("Vender os seguintes:")
print(bons_para_venda)
print()
print("Comprar os seguintes:")
print(bons_para_compra)
print()
print("#### SEM DADOS ######")
print(com_problema)

# msg = MIMEMultipart()
# msg['From'] = email_sender
# msg['To'] = email_receiver
# msg['Subject'] = f'Teste 1 para envio de lista de ativos'

# # Corpo do e-mail
# body = f"""
# Lista de ativos para compra:{bons_para_compra}

# Lista de ativos para venda:{bons_para_venda}

# Lista de ativos sem dados: {com_problema}
# """
# msg.attach(MIMEText(body, 'plain'))


# # Enviando o e-mail
# server.sendmail(email_sender, email_receiver, msg.as_string())
# server.quit()

# print("E-mail enviado com sucesso!")
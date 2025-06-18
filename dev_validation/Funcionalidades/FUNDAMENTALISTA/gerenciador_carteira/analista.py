from datetime import datetime, timedelta
from FUNDAMENTALISTA.conexao.conectar import Yfinance
from .carteira import Carteira
import time




class Analista:
    def __init__(self):
        self.tempos = ['1d','1h','1mo','1wk']
        self.data_atual = datetime.now()
        self.bons_para_compra = []
        self.bons_para_venda = []
        self.com_problema_nos_dados = []
        self.preco = {}
        self.buffers = {}
        self.count_downloads = 0   
        self.ativos_analizados = {}   
        self.yf = Yfinance()
        self.downloader = self.yf.conecta()
        self.carteira_class =  Carteira()

    def analizar_listas_de_ativos_subs(self, sub_listas):
       
        for sub_lista in sub_listas:
            ativos = sub_lista
        
            for tempo in self.tempos:
                for ativo in ativos:
                    try:
                        if tempo !='1h':
                            data_inicio = self.data_atual - timedelta(days=3000)
                        else:
                            data_inicio = self.data_atual - timedelta(days=500) 
                        # Obtendo os dados do ativo
                        dados_ativo = self.downloader.download(ativo, start=data_inicio, interval=tempo)

                        # Verificando se há dados disponíveis
                        if dados_ativo.empty:
                            raise ValueError(f"Nenhum dado disponível para {ativo}")

                        self.count_downloads += 1
                        if self.count_downloads % 100 == 0:
                            print("Aguardando 1 minuto antes de continuar...")
                            time.sleep(30)
                        # Calculando os retornos
                        dados_ativo['Retornos'] = dados_ativo['Adj Close'].pct_change().dropna()

                    except Exception as e:
                        self.com_problema_nos_dados.append(ativo)
                        print(f"Erro ao obter dados para {ativo}: {e}")
                        continue

                    def filtrando_retorno_positivo(x):
                        return x if x > 0 else 0

                    def filtrando_retorno_negativo(x):
                        return abs(x) if x < 0 else 0

                    dados_ativo['RetornosPositivos'] = dados_ativo['Retornos'].apply(
                        filtrando_retorno_positivo)
                    dados_ativo['RetornosNegativos'] = dados_ativo['Retornos'].apply(
                        filtrando_retorno_negativo)

                    dados_ativo['MediaMovelPositiva'] = dados_ativo['RetornosPositivos'].rolling(
                        window=14).mean()
                    dados_ativo['MediaMovelNegativa'] = dados_ativo['RetornosNegativos'].rolling(
                        window=21).mean()

                    dados_ativo['RSI'] = 100 - 100 / \
                        (1 + dados_ativo['MediaMovelPositiva'] /
                        dados_ativo['MediaMovelNegativa'])

                    periodo = 38
                    dados_ativo['SMA'] = dados_ativo['Adj Close'].rolling(
                        window=periodo).mean()
                    dados_ativo['DesvioPadrao'] = dados_ativo['Adj Close'].rolling(
                        window=periodo).std()
                    dados_ativo['BandaSuperior'] = dados_ativo['SMA'] + \
                        2.2 * dados_ativo['DesvioPadrao']
                    dados_ativo['BandaInferior'] = dados_ativo['SMA'] - \
                        0.9 * dados_ativo['DesvioPadrao']

                    dados_ativo.loc[(dados_ativo['Adj Close'] <
                                    dados_ativo['BandaInferior']), 'Sinal'] = 'COMPRA'
                    dados_ativo.loc[(dados_ativo['Adj Close'] >
                                    dados_ativo['BandaSuperior']), 'Sinal'] = 'VENDA'

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

                    dados_ativo.loc[(dados_ativo['Estocastico_8'] <= 20) & (
                        dados_ativo['Estocastico_30'] <= 20) & (dados_ativo['Estocastico'] <= 20), 'Sinal'] = 'COMPRA'

                    dados_ativo.loc[(dados_ativo['Estocastico_8'] >= 80) & (
                        dados_ativo['Estocastico_30'] >= 80) & (dados_ativo['Estocastico'] >= 80), 'Sinal'] = 'VENDA'

                    dados_ativo['MediaMovel14'] = dados_ativo['Adj Close'].rolling(
                        window=21).mean()
                    dados_ativo['MediaMovel21'] = dados_ativo['Adj Close'].rolling(
                        window=71).mean()

                    dados_ativo.loc[dados_ativo['Estocastico'] <= 20,
                                    'Estocastico_20'] = dados_ativo['Adj Close']
                    dados_ativo.loc[dados_ativo['Estocastico'] >= 80,
                                    'Estocastico_80'] = dados_ativo['Adj Close']
        
            
            if not dados_ativo.empty:
                ultimo_index = dados_ativo.index[-1]
                indice_agora = dados_ativo.index.get_loc(ultimo_index)
                print(indice_agora)
                if ultimo_index in dados_ativo.index:
                    indice_agora = dados_ativo.index.get_loc(ultimo_index)
                    print(indice_agora)
                    # Inicializa a chave do ativo se não existir
                    if ativo not in self.ativos_analizados:
                        self.ativos_analizados[ativo] = {}

                    if tempo not in self.ativos_analizados[ativo]:
                        self.ativos_analizados[ativo][tempo] = {}
                        
                    if dados_ativo.iloc[indice_agora]['Sinal'] == 'COMPRA':
                        self.ativos_analizados[ativo][tempo] = dados_ativo
                        self.bons_para_compra.append(ativo)
                        self.preco[ativo] = f"{dados_ativo.iloc[indice_agora]['Close']:.2f} Sinalizando compra!"
                        preco_operacao = dados_ativo.iloc[indice_agora]['Close']
                        qtd = self.carteira_class.dividir_caixa(self.carteira_class.carteira_df, ativo, preco_operacao)
                        if qtd > 0:
                            self.carteira_class.atualizar_total(ativo, preco_operacao, 'COMPRA', qtd)
                            self.carteira_class.registrar_operacao(ativo, preco_operacao, 'COMPRA', qtd, self.carteira_class.carteira_df.loc[0, 'PRECO_MEDIO'])
                    
                    if dados_ativo.iloc[indice_agora]['Sinal'] == 'VENDA':
                        self.ativos_analizados[ativo][tempo] = dados_ativo
                        self.bons_para_venda.append(ativo)
                        self.preco[ativo] = f"{dados_ativo.iloc[indice_agora]['Close']:.2f}Sinalizando venda!"
                        preco_operacao = dados_ativo.iloc[indice_agora]['Close']
                        qtd = self.carteira_class.dividir_caixa(self.carteira_class.carteira_df, ativo, preco_operacao)
                        if qtd > 0:
                            self.carteira_class.atualizar_total(ativo, preco_operacao, 'VENDA', qtd)
                            self.carteira_class.registrar_operacao(ativo, preco_operacao, 'VENDA', qtd, self.carteira_class.carteira_df.loc[0, 'PRECO_MEDIO'])
        return self.ativos_analizados, self.preco               
             
    def analizar_listas_de_ativos(self, lista):
        ativos = lista
    
        for tempo in self.tempos:
            for ativo in ativos:
                
                try:
                    if tempo !='1h':
                        data_inicio = self.data_atual - timedelta(days=3000)
                    else:
                        data_inicio = self.data_atual - timedelta(days=500) 
                    # Obtendo os dados do ativo
                    dados_ativo = self.downloader.download(ativo, start=data_inicio, interval=tempo)

                    # Verificando se há dados disponíveis
                    if dados_ativo.empty:
                        raise ValueError(f"Nenhum dado disponível para {ativo}")

                    self.count_downloads += 1
                    if self.count_downloads % 100 == 0:
                        print("Aguardando 1 minuto antes de continuar...")
                        time.sleep(30)
                    # Calculando os retornos
                    dados_ativo['Retornos'] = dados_ativo['Adj Close'].pct_change().dropna()

                except Exception as e:
                    self.com_problema_nos_dados.append(ativo)
                    print(f"Erro ao obter dados para {ativo}: {e}")
                    continue

                def filtrando_retorno_positivo(x):
                    return x if x > 0 else 0

                def filtrando_retorno_negativo(x):
                    return abs(x) if x < 0 else 0

                dados_ativo['RetornosPositivos'] = dados_ativo['Retornos'].apply(
                    filtrando_retorno_positivo)
                dados_ativo['RetornosNegativos'] = dados_ativo['Retornos'].apply(
                    filtrando_retorno_negativo)

                dados_ativo['MediaMovelPositiva'] = dados_ativo['RetornosPositivos'].rolling(
                    window=14).mean()
                dados_ativo['MediaMovelNegativa'] = dados_ativo['RetornosNegativos'].rolling(
                    window=21).mean()

                dados_ativo['RSI'] = 100 - 100 / \
                    (1 + dados_ativo['MediaMovelPositiva'] /
                    dados_ativo['MediaMovelNegativa'])

                periodo = 38
                dados_ativo['SMA'] = dados_ativo['Adj Close'].rolling(
                    window=periodo).mean()
                dados_ativo['DesvioPadrao'] = dados_ativo['Adj Close'].rolling(
                    window=periodo).std()
                dados_ativo['BandaSuperior'] = dados_ativo['SMA'] + \
                    2.2 * dados_ativo['DesvioPadrao']
                dados_ativo['BandaInferior'] = dados_ativo['SMA'] - \
                    0.9 * dados_ativo['DesvioPadrao']

                dados_ativo.loc[(dados_ativo['Adj Close'] <
                                dados_ativo['BandaInferior']), 'Sinal'] = 'COMPRA'
                dados_ativo.loc[(dados_ativo['Adj Close'] >
                                dados_ativo['BandaSuperior']), 'Sinal'] = 'VENDA'

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

                dados_ativo.loc[(dados_ativo['Estocastico_8'] <= 20) & (
                    dados_ativo['Estocastico_30'] <= 20) & (dados_ativo['Estocastico'] <= 20), 'Sinal'] = 'COMPRA'

                dados_ativo.loc[(dados_ativo['Estocastico_8'] >= 80) & (
                    dados_ativo['Estocastico_30'] >= 80) & (dados_ativo['Estocastico'] >= 80), 'Sinal'] = 'VENDA'

                dados_ativo['MediaMovel14'] = dados_ativo['Adj Close'].rolling(
                    window=21).mean()
                dados_ativo['MediaMovel21'] = dados_ativo['Adj Close'].rolling(
                    window=71).mean()

                dados_ativo.loc[dados_ativo['Estocastico'] <= 20,
                                'Estocastico_20'] = dados_ativo['Adj Close']
                dados_ativo.loc[dados_ativo['Estocastico'] >= 80,
                                'Estocastico_80'] = dados_ativo['Adj Close']
        
            if not dados_ativo.empty:
                ultimo_index = dados_ativo.index[-1]
                indice_agora = dados_ativo.index.get_loc(ultimo_index)
                print(indice_agora)
                if ultimo_index in dados_ativo.index:
                    indice_agora = dados_ativo.index.get_loc(ultimo_index)
                    print(indice_agora)
                    
                    # Inicializa a chave do ativo se não existir
                    if ativo not in self.ativos_analizados:
                        self.ativos_analizados[ativo] = {}

                    if tempo not in self.ativos_analizados[ativo]:
                        self.ativos_analizados[ativo][tempo] = {}
                        
                    if dados_ativo.iloc[indice_agora]['Sinal'] == 'COMPRA':
                        self.ativos_analizados[ativo][tempo] = dados_ativo
                        self.bons_para_compra.append(ativo)
                        print(self.ativos_analizados[ativo][tempo])
                        breakpoint()
                        self.preco[ativo] = f"{dados_ativo.iloc[indice_agora]['Close']:.2f} Sinalizando compra!"
                        preco_operacao = dados_ativo.iloc[indice_agora]['Close']
                        qtd = self.carteira_class.dividir_caixa(self.carteira_class.carteira_df, ativo, preco_operacao)
                        if qtd > 0:
                            self.carteira_class.atualizar_total(ativo, preco_operacao, 'COMPRA', qtd)
                            self.carteira_class.registrar_operacao(ativo, preco_operacao, 'COMPRA', qtd, self.carteira_class.carteira_df.loc[0, 'PRECO_MEDIO'])
                    
                    if dados_ativo.iloc[indice_agora]['Sinal'] == 'VENDA':
                        self.ativos_analizados[ativo][tempo] = dados_ativo
                        print(self.ativos_analizados[ativo][tempo])
                        breakpoint()
                        self.bons_para_venda.append(ativo)
                        self.preco[ativo] = f"{dados_ativo.iloc[indice_agora]['Close']:.2f}Sinalizando venda!"
                        preco_operacao = dados_ativo.iloc[indice_agora]['Close']
                        print(preco_operacao)
                        qtd = self.carteira_class.dividir_caixa(self.carteira_class.carteira_df, ativo, preco_operacao)
                        if qtd > 0:
                            self.carteira_class.atualizar_total(ativo, preco_operacao, 'VENDA', qtd)
                            self.carteira_class.registrar_operacao(ativo, preco_operacao, 'VENDA', qtd, self.carteira_class.carteira_df.loc[0, 'PRECO_MEDIO'])
        
        return self.ativos_analizados, self.preco


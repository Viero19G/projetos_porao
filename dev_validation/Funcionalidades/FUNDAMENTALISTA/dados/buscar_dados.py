from FUNDAMENTALISTA.conexao.conectar import Yfinance as conect
from datetime import datetime, timedelta
import pandas as pd
import xlsxwriter
import time  # Importe a biblioteca time


class BuscarCodes:
    def __init__(self):
        self.conectar = conect.conecta()
        
        # usado para buscar os ticker, que são os dados
    def get_tickers(self,ativos):
        todos_tickers = {}
        for ativo in ativos:
            codes = self.conectar.Ticker(ativo)
            todos_tickers[ativo] = codes
        return todos_tickers
    
    
    #-------------------------------------------------------------------------------------------------#
        # Usado para buscar o DRE
        # Algumas contas não podem ser trazidas para as normas do CPC
        #O IFRS (International Financial Reporting Standards) é um conjunto 
        # de normas contábeis internacionais publicadas pelo International
        # Accounting Standards Board (IASB). Essas normas estabelecem princípios
        # contábeis e requisitos de divulgação que empresas de todo o mundo devem
        # seguir ao preparar e apresentar suas demonstrações financeiras.
        #-------------------------------------------------------------------------------------------------#
    def dre_porLista(self,dicionario):
        dre_resultados = {}
        for ativo, objeto_ticker in dicionario.items():
            dre = objeto_ticker.get_financials(freq="quarterly")
            dre = pd.DataFrame(dre)
            dre = dre/1000
            # invertendo colunas para o gráfico não ficar invertido
            dre = dre[dre.columns[::-1]]
            dre_resultados[ativo] = dre
        return dre_resultados
    
    # Balanco patrimonial
    def balanco_patrimonial(self,dicionario):
        balanco_resultados = {}
        for ativo, objeto_ticker in dicionario.items():
            bal = objeto_ticker.get_balance_sheet(freq="yearly")
            bal = pd.DataFrame(bal)
            bal = bal/1000
            # invertendo colunas para o gráfico não ficar invertido
            bal = bal[bal.columns[::-1]]
            balanco_resultados[ativo] = bal
             # Criar um arquivo XLSX com o nome do ativo
        #     nome_arquivo = f"{ativo}.xlsx"
        #     writer = pd.ExcelWriter(nome_arquivo, engine='xlsxwriter')
        #     bal.to_excel(writer, index=False, sheet_name='Balanço Patrimonial')
        
        # # Salvar o arquivo
        #     writer.close()
        return balanco_resultados
    
        # o parametro esperado por empresa é o codigo CVM da mesma
    def busca_por_empresa(self, empresa):
        data_final = datetime.now()
        data_inicial = data_final - timedelta(days=600)
        # Abaixo cods para categorias DFP, ITR e Fatos Relevantes
        category = ["EST_4", "EST_3", "IPE_4_-1_-1"]
        last_ref_date = False
        busca = self.conectar.get_consulta_externa_cvm_results(
            cod_cvm=empresa,
            start_date=data_inicial,
            end_date=data_final,
            last_ref_date=last_ref_date,
            category=category
        )
        
        return busca
    
class BuscarCodesPy:
    def __init__(self):
        self.ipy = conect.conect_investPy()
    
    def get_tickersPy(self, ativos):
        ativos_com_country = {}
        for stock in ativos:
            info = self.ipy.stocks.get_stock_information(stock, as_json=False)
            country = info['Country']
            ativos_com_country[stock] = {'country': country}
        return ativos_com_country
    
    def dre_porListaPy(self, dicionario):
        dre_resultados = {}
        for ativo, info in dicionario.items():
            country = info['country']
            try:
                dre = self.ipy.get_stock_financial_summary(stock=ativo, country=country, summary_type='income_statement', period='annual')
                dre = dre.set_index('Indicator')
                dre_resultados[ativo] = dre
                time.sleep(30)  # Espere 30 segundos após cada requisição
            except Exception as e:
                print(f"Não foi possível obter informações para {ativo}, /n {e}")
        return dre_resultados
    
    def balanco_patrimonialPy(self, dicionario):
        balanco_resultados = {}
        for ativo, info in dicionario.items():
            country = info['country']
            try:
                bal = self.ipy.get_stock_financial_summary(stock=ativo, country=country, summary_type='balance_sheet', period='annual')
                bal = bal.set_index('Year')
                balanco_resultados[ativo] = bal
                time.sleep(30)  # Espere 30 segundos após cada requisição
            except:
                print(f"Não foi possível obter informações de balanço patrimonial para {ativo}")
        return balanco_resultados
    
    def get_primary_country(self, search_result):
        # Verifica se há mais de um país associado ao ativo
        if len(search_result['country'].unique()) > 1:
            # Seleciona o país com a contagem mais alta
            primary_country = search_result['country'].value_counts().idxmax()
        else:
            # Se houver apenas um país, seleciona esse país
            primary_country = search_result['country'].iloc[0]
        return primary_country

    def get_country_of_stock(self, dicionario):
        resultados_country = {}
        for ativo, dados in dicionario.items():
            try:
                search_result = self.ipy.stocks.search_stocks(by='symbol', value=ativo)
                if not search_result.empty:
                    # Obtém o país principal
                    primary_country = self.get_primary_country(search_result)
                    resultados_country[ativo] = {'dados': dados, 'country': primary_country}
                else:
                    resultados_country[ativo] = {'dados': dados, 'country': 'Vazio'}
            except Exception as e:
                print(f"Erro ao buscar informações do ativo: {e}")
        return resultados_country
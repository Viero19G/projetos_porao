import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import pandas as pd

class Grafico:
    def cria_grafico_para_email(self,ativo,dados_ativo):
        if not isinstance(dados_ativo, pd.DataFrame):
            dados_ativo = pd.DataFrame(dados_ativo)
        print(dados_ativo)
        filename = f"{ativo}.png"
        fig, axs = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

        axs[0].plot(dados_ativo.index, dados_ativo['Adj Close'],
                    label='Preço de Fechamento', color='black')
        axs[0].plot(dados_ativo.index, dados_ativo['MediaMovel14'],
                    label='Média Móvel 14', color='blue')
        axs[0].plot(dados_ativo.index, dados_ativo['MediaMovel21'],
                    label='Média Móvel 21', color='red')
        axs[0].scatter(dados_ativo.index, dados_ativo['Estocastico_20'],
                    label='Estocástico <= 20', color='yellow', marker='o', s=100)
        axs[0].scatter(dados_ativo.index, dados_ativo['Estocastico_80'],
                    label='Estocástico >= 80', color='orange', marker='o', s=100)
        axs[0].scatter(dados_ativo[dados_ativo['Sinal'] == 'COMPRA'].index, dados_ativo[dados_ativo['Sinal']
                    == 'COMPRA']['Adj Close'], label='COMPRA', color='green', marker='^', s=100)
        axs[0].scatter(dados_ativo[dados_ativo['Sinal'] == 'VENDA'].index, dados_ativo[dados_ativo['Sinal']
                    == 'VENDA']['Adj Close'], label='VENDA', color='red', marker='v', s=100)
        axs[0].plot(dados_ativo.index, dados_ativo['BandaSuperior'],
                    label='Banda Superior', color='purple', linestyle='--')
        axs[0].plot(dados_ativo.index, dados_ativo['BandaInferior'],
                    label='Banda Inferior', color='green', linestyle='--')
        axs[0].title.set_text(
            'Preço de Fechamento, Médias Móveis, Estocástico e Sinais')
        axs[0].set_ylabel('Preço de Fechamento')
        axs[0].legend()

        axs[1].plot(dados_ativo.index, dados_ativo['Estocastico'],
                    label='Estocástico', color='black')
        axs[1].plot(dados_ativo.index, dados_ativo['Estocastico'].rolling(
            window=1).mean(), label='SMTHK = 1', color='blue')
        axs[1].plot(dados_ativo.index, dados_ativo['Estocastico'].rolling(
            window=3).mean(), label='SMTHD = 3', color='red')
        axs[1].axhline(y=20, color='gray', linestyle='--')
        axs[1].axhline(y=80, color='gray', linestyle='--')
        axs[1].title.set_text(
            'Estocástico com SMTHK = 1, SMTHD = 3, e Length = 140')
        axs[1].set_xlabel('Data')
        axs[1].set_ylabel('Estocástico')
        axs[1].legend()

        axs[2].plot(dados_ativo.index, dados_ativo['Estocastico_30'],
                    label='Estocástico_30', color='black')
        axs[2].plot(dados_ativo.index, dados_ativo['Estocastico_30'].rolling(
            window=1).mean(), label='SMTHK = 1', color='blue')
        axs[2].plot(dados_ativo.index, dados_ativo['Estocastico_30'].rolling(
            window=3).mean(), label='SMTHD = 3', color='red')
        axs[2].axhline(y=20, color='gray', linestyle='--')
        axs[2].axhline(y=80, color='gray', linestyle='--')
        axs[2].title.set_text(
            'Estocástico com SMTHK = 1, SMTHD = 3, e Length = 30')
        axs[2].set_xlabel('Data')
        axs[2].set_ylabel('Estocástico_30')
        axs[2].legend()

        axs[3].plot(dados_ativo.index, dados_ativo['Estocastico_8'],
                    label='Estocástico_8', color='black')
        axs[3].plot(dados_ativo.index, dados_ativo['Estocastico_8'].rolling(
            window=1).mean(), label='SMTHK = 1', color='blue')
        axs[3].plot(dados_ativo.index, dados_ativo['Estocastico_8'].rolling(
            window=3).mean(), label='SMTHD = 3', color='red')
        axs[3].axhline(y=20, color='gray', linestyle='--')
        axs[3].axhline(y=80, color='gray', linestyle='--')
        axs[3].title.set_text('Estocástico com SMTHK = 1, SMTHD = 3, e Length = 8')
        axs[3].set_xlabel('Data')
        axs[3].set_ylabel('Estocástico_8')
        axs[3].legend()
        plt.savefig(filename)
        plt.close(fig)
    
        return filename
        
    def cria_grafico(self, dre_lista, lista_balanco_s, grau_endividamento):
        for ativo, objeto_ticker_dre in dre_lista.items():
            dre = objeto_ticker_dre
            if ativo in lista_balanco_s:  # Verifica se o ativo está presente em lista_balanco_s
                objeto_ticker_balanco = lista_balanco_s[ativo]
                balanco = objeto_ticker_balanco
                print(balanco)
                breakpoint()
            if ativo in grau_endividamento:  # Verifica se o ativo está presente em lista_balanco_s
                objeto = grau_endividamento[ativo]
                valores = objeto
                fig = make_subplots(rows=3, cols=3, row_heights=[5, 5, 5],
                                    column_widths=[3, 3, 3], subplot_titles=('EBITDA', 'Lucro líquido','Caixa e Equivalentes de Caixa',
                                                                        'Dívida Líquida', 'Dívida Total','Ativos Totais',
                                                                        'Passivo Circulante','Ativos Circulantes',f'Endividamento {ativo}'), shared_xaxes=False)
                fig.add_trace(go.Bar(name='EBITDA', x=dre.columns, y=dre.loc['EBITDA']), row=1, col=1)
                fig.add_trace(go.Bar(name='Lucro líquido', x=dre.columns, y=dre.loc['NetIncome']), row=1, col=2)

                fig.add_trace(go.Bar(name='Caixa e Equivalentes de Caixa', x=balanco.columns, y=balanco.loc['CashAndCashEquivalents']), row=1, col=3)
                fig.add_trace(go.Bar(name='Ativos Totais', x=balanco.columns, y=balanco.loc['TotalAssets']), row=2, col=3)
                fig.add_trace(go.Bar(name='Passivo Circulante', x=balanco.columns, y=balanco.loc['CurrentLiabilities']), row=3, col=1)
                fig.add_trace(go.Bar(name='Ativos Circulantes', x=balanco.columns, y=balanco.loc['CurrentAssets']), row=3, col=2)
                fig.add_trace(go.Bar(name=f'Endividamento {ativo}',x=valores.index, y=valores.values), row=3, col=3)
                fig.add_trace(go.Bar(name='Dívida Líquida', x=balanco.columns, y=balanco.loc['NetDebt']), row=2, col=1)
                fig.add_trace(go.Bar(name='Dívida Total', x=balanco.columns, y=balanco.loc['TotalDebt']), row=2, col=2)

                fig.update_layout(title_text=f'<b> Avaliação fundamentalista {ativo} !!! <b>',
                                template='plotly_dark',
                                showlegend=False,
                                height=500,
                                width=800)
                fig.show()
            else:
                print(f"Ativo {ativo} não encontrado em lista_balanco_s")
        return
    
    def cria_grafico_dinamico(self, dre_lista, lista_balanco_s, grau_endividamento):
        for ativo, objeto_ticker_dre in dre_lista.items():
            dre = objeto_ticker_dre
            if ativo in lista_balanco_s:  # Verifica se o ativo está presente em lista_balanco_s
                objeto_ticker_balanco = lista_balanco_s[ativo]
                balanco = objeto_ticker_balanco
            if ativo in grau_endividamento:  # Verifica se o ativo está presente em lista_balanco_s
                objeto = grau_endividamento[ativo]
                valores = objeto
                fig = make_subplots(rows=3, cols=3, row_heights=[5, 5, 5],
                                    column_widths=[3, 3, 3], subplot_titles=('EBITDA', 'Lucro líquido','Caixa e Equivalentes de Caixa',
                                                                        'Dívida Líquida', 'Dívida Total','Ativos Totais',
                                                                        'Passivo Circulante','Ativos Circulantes',f'Endividamento {ativo}'), shared_xaxes=False)
                fig.add_trace(go.Bar(name='EBITDA', x=dre.columns, y=dre.loc['EBITDA']), row=1, col=1)
                fig.add_trace(go.Bar(name='Lucro líquido', x=dre.columns, y=dre.loc['NetIncome']), row=1, col=2)

                fig.add_trace(go.Bar(name='Caixa e Equivalentes de Caixa', x=balanco.columns, y=balanco.loc['CashAndCashEquivalents']), row=1, col=3)
                fig.add_trace(go.Bar(name='Ativos Totais', x=balanco.columns, y=balanco.loc['TotalAssets']), row=2, col=3)
                fig.add_trace(go.Bar(name='Passivo Circulante', x=balanco.columns, y=balanco.loc['CurrentLiabilities']), row=3, col=1)
                fig.add_trace(go.Bar(name='Ativos Circulantes', x=balanco.columns, y=balanco.loc['CurrentAssets']), row=3, col=2)
                fig.add_trace(go.Bar(name=f'Endividamento {ativo}',x=valores.index, y=valores.values), row=3, col=3)
                fig.add_trace(go.Bar(name='Dívida Líquida', x=balanco.columns, y=balanco.loc['NetDebt']), row=2, col=1)
                fig.add_trace(go.Bar(name='Dívida Total', x=balanco.columns, y=balanco.loc['TotalDebt']), row=2, col=2)

                fig.update_layout(title_text=f'<b> Avaliação fundamentalista {ativo} !!! <b>',
                                template='plotly_dark',
                                showlegend=False,
                                height=500,
                                width=800)
                fig.show()
            else:
                print(f"Ativo {ativo} não encontrado em lista_balanco_s")
        return

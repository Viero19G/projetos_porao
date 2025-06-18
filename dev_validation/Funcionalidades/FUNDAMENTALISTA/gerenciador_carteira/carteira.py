import pandas as pd
from datetime import datetime, timedelta
pd.options.mode.chained_assignment = None

class Carteira:
    def __init__(self):
        self.carteira_path = r'C:\gerenciador_carteira\carteira.xlsx'
        self.historia_path = r'C:\gerenciador_carteira\historico.xlsx'
        self.carteira_df, self.historia_df = self.CarregarDadosCarteira(self.carteira_path, self.historia_path)
    

    def CarregarDadosCarteira(self, carteira, historico):
        #Carregar arquivos.
        carteira_df = pd.read_excel(carteira, dtype={'ATIVOS':str})
        historia_df = pd.read_excel(historico)

        # Verificar o conteúdo do DataFrame carregado
        print("Conteúdo do TOTAL.xlsx após carregamento:")
        print(carteira_df)

        # Garantir que a coluna PRECO_MEDIO está presente
        if 'PRECO_MEDIO' not in carteira_df.columns:
            carteira_df['PRECO_MEDIO'] = 0

        # Garantir que a linha 0 está presente
        if carteira_df.empty:
            carteira_df = pd.DataFrame({'ATIVOS': [''], 'QTD': [0], 'CAIXA': [1000], 'TOTAL': [0], 'PRECO_MEDIO': [0]})

        # Garantir que a coluna ATIVOS não contenha NaN
        carteira_df['ATIVOS'] = carteira_df['ATIVOS'].fillna('')
        
        return carteira_df, historia_df
    
    def dividir_caixa(self, carteira_df, ativo, preco):
        caixa_atual = carteira_df.loc[0, 'CAIXA']
        ativos_list = [a.strip() for a in carteira_df.loc[0, 'ATIVOS'].split(',') if a.strip()]
        num_ativos = len(ativos_list) + (1 if ativo not in ativos_list else 0)
        
        if num_ativos > 0:
            limite_por_ativo = caixa_atual / num_ativos
            qtd_maxima = int(limite_por_ativo // preco)
            print(f"Quantidade ajustada para {qtd_maxima} unidades de {ativo}.")
            return qtd_maxima
        return 0
    
    # Função para atualizar o arquivo TOTAL.xlsx
    def atualizar_total(self,ativo, preco, operacao, qtd):
        
        if operacao == 'COMPRA':
            self.carteira_df.loc[0, 'CAIXA'] -= preco * qtd
            if ativo in self.carteira_df.loc[0, 'ATIVOS']:
                # Atualizar preço médio
                qtd_atual = self.carteira_df.loc[0, 'QTD']
                preco_medio_atual = self.carteira_df.loc[0, 'PRECO_MEDIO']
                novo_preco_medio = ((preco_medio_atual * qtd_atual) + (preco * qtd)) / (qtd_atual + qtd)
                self.carteira_df.loc[0, 'PRECO_MEDIO'] = novo_preco_medio
                self.carteira_df.loc[0, 'QTD'] += qtd
            else:
                self.carteira_df.loc[0, 'ATIVOS'] = f"{self.carteira_df.loc[0, 'ATIVOS']},{ativo}" if self.carteira_df.loc[0, 'ATIVOS'] else ativo
                self.carteira_df.loc[0, 'QTD'] += qtd
                self.carteira_df.loc[0, 'PRECO_MEDIO'] = preco
        elif operacao == 'VENDA':
            if ativo not in self.carteira_df.loc[0, 'ATIVOS']:
                print(f"Ativo {ativo} não encontrado na carteira.")
                return
            self.carteira_df.loc[0, 'CAIXA'] += preco * qtd
            self.carteira_df.loc[0, 'QTD'] -= qtd
            if self.carteira_df.loc[0, 'QTD'] == 0:
                ativos_list = self.carteira_df.loc[0, 'ATIVOS'].split(',')
                ativos_list.remove(ativo)
                self.carteira_df.loc[0, 'ATIVOS'] = ','.join(ativos_list)
                self.carteira_df.loc[0, 'PRECO_MEDIO'] = 0
        self.carteira_df.loc[0, 'TOTAL'] = self.carteira_df.loc[0, 'CAIXA'] + (self.carteira_df.loc[0, 'QTD'] * self.carteira_df.loc[0, 'PRECO_MEDIO'])
        self.carteira_df.to_excel(self.carteira_df, index=False)

    
        # Função para registrar a operação no HISTORIA.xlsx
    def registrar_operacao(self, ativo, preco, operacao, qtd, preco_medio):
        tempo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_row = pd.DataFrame({'ATIVO': [ativo], 'PRECO': [preco], 'OPERACAO': [operacao], 'TEMPO': [tempo], 'QTD': [qtd], 'PRECO_MEDIO': [preco_medio]})
        self.historia_df = pd.concat([self.historia_df, new_row], ignore_index=True)
        self.historia_df.to_excel(self.historia_df, index=False)

    # Função para imprimir os ativos separadamente
    def acessar_carteira(self):
        ativos_list = [a.strip() for a in self.carteira_df.loc[0, 'ATIVOS'].split(',') if a.strip()]
        # for ativo in ativos_list:
        #     print(f"Ativo: {ativo}")
        return ativos_list
    
    def dividir_em_sublistas(self,lista, tamanho_maximo):
        sub_listas = []  # Lista para armazenar as sub-listas
        sub_lista_atual = []  # Lista temporária para armazenar os elementos da sub-lista atual

        for elemento in lista:
            # Adiciona o elemento à sub-lista atual
            sub_lista_atual.append(elemento)

            if len(sub_lista_atual) == tamanho_maximo:
                # Adiciona a sub-lista atual à lista de sub-listas
                sub_listas.append(sub_lista_atual)
                sub_lista_atual = []  # Reinicia a sub-lista atual

        # Se houver elementos restantes na sub-lista atual, adiciona-os à lista de sub-listas
        if sub_lista_atual:
            sub_listas.append(sub_lista_atual)

        return sub_listas
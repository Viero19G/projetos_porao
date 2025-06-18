import os
import pandas as pd

class GerenciadorArquivos:
    def __init__(self):
        pass
    def criar_arquivos_iniciais(self):
        carteira_path = r'C:\gerenciador_carteira\carteira.xlsx'
        historia_path = r'C:\gerenciador_carteira\historico.xlsx'
        if not os.path.exists(carteira_path):
            total_data = {'ATIVOS': [''], 'QTD': [0], 'CAIXA': [1000], 'TOTAL': [0], 'PRECO_MEDIO': [0]}
            total_df = pd.DataFrame(total_data)
            total_df.to_excel(carteira_path, index=False)

        if not os.path.exists(historia_path):
            historia_data = {'ATIVO': [], 'PRECO': [], 'OPERACAO': [], 'TEMPO': [], 'QTD': [], 'PRECO_MEDIO': []}
            historia_df = pd.DataFrame(historia_data)
            historia_df.to_excel(historia_path, index=False)
        
        return carteira_path, historia_path
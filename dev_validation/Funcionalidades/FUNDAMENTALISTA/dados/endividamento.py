

class Calculos:
    def __init__(self):
        return
    ## Analise baseada na PETR4 e deve receber a planilha de balanço para realizar o calculo
    def calcular_grau_endividamento(self, dicionario_balancos):
        calculados = {}
        for ativo, balanco in dicionario_balancos.items():
            df_balance_sheet = balanco
            # Selecionar as contas relacionadas ao endividamento
            contas_endividamento = [
                'TotalDebt',
                'CapitalLeaseObligations',
                'LongTermDebt',
                'CurrentDebt'
            ]
            
            # Calcular o total de dívidas somando as contas relacionadas ao endividamento
            total_dividas = df_balance_sheet.loc[contas_endividamento].sum()
            
            # Calcular o patrimônio líquido como a diferença entre os ativos totais e os passivos totais
            total_ativos = df_balance_sheet.loc['TotalAssets']
            total_passivos = df_balance_sheet.loc['TotalLiabilitiesNetMinorityInterest']
            patrimonio_liquido = total_ativos - total_passivos
            
            # Calcular o Grau de Endividamento dividindo o total de dívidas pelo patrimônio líquido
            grau_endividamento = total_dividas / patrimonio_liquido
            
            calculados[ativo] = grau_endividamento
        return calculados
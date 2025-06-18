import yfinance as yf
import json
import pandas as pd

pd.set_option("display.max_rows", None)

def buscar_balanco(ticker):
    try:
        empresa = yf.Ticker(ticker)
        balanco = empresa.balance_sheet.fillna(0)  # Substitui NaN por 0
        balanco.index = balanco.index.str.replace(' ', '')  # Remove espaços dos índices
        print(f"DataFrame do balanço para o ticker {ticker}:")
        print(balanco)  # Imprime o DataFrame para verificar se está correto
        return balanco
    except Exception as e:
        print(f"Erro ao buscar o balanço para o ticker {ticker}: {e}")
        return None

def buscar_fluxo_de_caixa(ticker):
    try:
        empresa = yf.Ticker(ticker)
        cash = empresa.cash_flow.fillna(0)  # Substitui NaN por 0
        cash.index = cash.index.str.replace(' ', '')  # Remove espaços dos índices
        print(f"DataFrame do fluxo de caixa para o ticker {ticker}:")
        print(cash)
        return cash
    except Exception as e:
        print(f"Erro ao buscar o fluxo de caixa para o ticker {ticker}: {e}")
        return None

def buscar_dre(ticker):
    try:
        empresa = yf.Ticker(ticker)
        dre = empresa.financials.fillna(0)  # Substitui NaN por 0
        dre.index = dre.index.str.replace(' ', '')  # Remove espaços dos índices
        print(f"DataFrame da Demonstração de Resultados para o ticker {ticker}:")
        print(dre)
        # dre.to_excel(f"{ticker}_DRE.xlsx") # Imprime o DataFrame para verificar se está correto
        return dre
    except Exception as e:
        print(f"Erro ao buscar a Demonstração de Resultados para o ticker {ticker}: {e}")
        return None

def processar_conta(df_balanco, conta, subcontas, ano, ticker):
    conta_organizada = {}
    valor_conta = 0 

    if conta in df_balanco.index:
        valor_conta = df_balanco.at[conta, ano]
    elif conta == 'Cash':
        valor_conta = df_balanco.loc['CashAndCashEquivalents',ano] - df_balanco.loc['CashEquivalents', ano]
    elif conta == 'MineralProperties':
        valor_conta = df_balanco.loc['GrossPPE',ano] - (df_balanco.loc['LandAndImprovements', ano] + df_balanco.loc['MachineryFurnitureEquipment', ano] + df_balanco.loc['OtherProperties', ano] + df_balanco.loc['ConstructionInProgress', ano] + df_balanco.loc['Leases', ano])
    elif conta == 'OperationAndMaintenance':    
        valor_conta = df_balanco.loc['OperatingExpense',ano] - (df_balanco.loc['SellingGeneralAndAdministration', ano] + df_balanco.loc['ResearchAndDevelopment', ano] + df_balanco.loc['DepreciationAmortizationDepletionIncomeStatement', ano] + df_balanco.loc['ProvisionForDoubtfulAccounts', ano] + df_balanco.loc['OtherTaxes', ano] + df_balanco.loc['OtherOperatingExpenses', ano])
        print(valor_conta)
        

    conta_organizada['valor'] = valor_conta if pd.notna(valor_conta) else 0

    soma_subcontas = 0
    for chave, subchaves in subcontas.items():
        if isinstance(subchaves, dict):
            subconta_organizada = processar_conta(df_balanco, chave, subchaves, ano, ticker)
            soma_subcontas += subconta_organizada.get('valor', 0)
            conta_organizada[chave] = subconta_organizada
        else:
            valor_subconta = 0
            if chave in df_balanco.index:
                valor_subconta = df_balanco.at[chave, ano]
            conta_organizada[chave] = valor_subconta if pd.notna(valor_subconta) else 0
            soma_subcontas += conta_organizada[chave]

  
    return conta_organizada

def organizar(df_balanco, estrutura_json, ticker):
    anos = df_balanco.columns
    balancos_por_ano = {}

    for ano in anos:
        balanco_organizado = {}
        for conta, subcontas in estrutura_json.items():
            balanco_organizado[conta] = processar_conta(df_balanco, conta, subcontas, ano, ticker)
        balancos_por_ano[ano.strftime('%Y-%m-%d')] = balanco_organizado

    return balancos_por_ano

def validar_coerencia(balanco_organizado, estrutura_json):
    def validar_conta(conta_organizada, estrutura_json):
        for conta, valores in conta_organizada.items():
            if 'valor' in valores:
                subcontas = estrutura_json.get(conta, {})
                soma_subcontas = 0
                for subconta in subcontas:
                    if subconta != 'valor':
                        if isinstance(valores[subconta], dict):
                            soma_subcontas += valores[subconta].get('valor', 0) or 0
                        else:
                            soma_subcontas += valores.get(subconta, 0) or 0
                if valores['valor'] != soma_subcontas:
                    print(f"A conta '{conta}' tem valor {valores['valor']}, mas a soma das subcontas é {soma_subcontas}.")

    for contas in balanco_organizado.values():
        validar_conta(contas, estrutura_json)

def main():
    try:
        with open(r'C:\Users\gabri\Documents\projetos_python\Projeto_II\MAIN\FUNDAMENTALISTA\dados\contas.json', 'r') as file:
            estrutura_json = json.load(file)
    except Exception as e:
        print(f"Erro ao carregar o arquivo JSON: {e}")
        return
    
    try:
        with open(r'C:\Users\gabri\Documents\projetos_python\Projeto_II\MAIN\FUNDAMENTALISTA\dados\fluxo_caixa.json', 'r') as file:
            estrutura_json_cash = json.load(file)
    except Exception as e:
        print(f"Erro ao carregar o arquivo JSON: {e}")
        return
    
    try:
        with open(r'C:\Users\gabri\Documents\projetos_python\Projeto_II\MAIN\FUNDAMENTALISTA\dados\dre.json', 'r') as file:
            estrutura_json_dre = json.load(file)
    except Exception as e:
        print(f"Erro ao carregar o arquivo JSON: {e}")
        return

    ticker = "PETR4.SA"
    df_balanco = buscar_balanco(ticker)
    df_cash_flow = buscar_fluxo_de_caixa(ticker)
    df_dre = buscar_dre(ticker)
    
    if df_balanco is None or df_cash_flow is None:
        return

    balancos_organizados = organizar(df_balanco, estrutura_json, ticker)
    cash_organizados = organizar(df_cash_flow, estrutura_json_cash, ticker)
    dre_organizados = organizar(df_dre, estrutura_json_dre, ticker)
    
    validar_coerencia(balancos_organizados, estrutura_json)
    validar_coerencia(cash_organizados, estrutura_json_cash)
    validar_coerencia(dre_organizados, estrutura_json_dre)

    for ano, balanco in balancos_organizados.items():
        try:
            with open(f'balanco_organizado_{ano}.json', 'w') as file:
                json.dump(balanco, file, indent=4)
        except Exception as e:
            print(f"Erro ao salvar o arquivo JSON para o ano {ano}: {e}")
    for ano, cash in cash_organizados.items():
        try:
            with open(f'cash_organizado_{ano}.json', 'w') as file:
                json.dump(cash, file, indent=4)
        except Exception as e:
            print(f"Erro ao salvar o arquivo JSON para o ano {ano}: {e}")
    for ano, dre in dre_organizados.items():
        try:
            with open(f'dre_organizado_{ano}.json', 'w') as file:
                json.dump(dre, file, indent=4)
        except Exception as e:
            print(f"Erro ao salvar o arquivo JSON para o ano {ano}: {e}")

if __name__ == "__main__":
    main()

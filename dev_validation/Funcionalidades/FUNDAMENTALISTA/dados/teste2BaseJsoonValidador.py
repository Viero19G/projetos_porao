import yfinance as yf
import json
import pandas as pd

pd.set_option("display.max_rows", None)
############################# Validação de total Assets TESTE ########################################


def somar_valores(dicionario):
    soma = 0
    for chave, valor in dicionario.items():
        if isinstance(valor, dict):
            # Se o valor for um dicionário, chama a função recursivamente
            soma += somar_valores(valor)
        elif isinstance(valor, (int, float)):
            # Se o valor for um número, soma
            soma += valor
    return soma

def validar_total_assets(json_data):
    total_assets_valor = json_data.get("TOTALASSETS", {}).get("valor", 0)
    
    # Calcula a soma de todas as subchaves, exceto a chave "valor" de TOTALASSETS
    soma_subchaves = somar_valores(json_data.get("TOTALASSETS", {})) - total_assets_valor
    
    # Verifica se o valor de TOTALASSETS é igual à soma de todas as suas subchaves
    if total_assets_valor == soma_subchaves:
        print("Validação bem-sucedida: A soma das subchaves é igual ao valor de TOTALASSETS.")
        print(f"TOTALASSETS = {total_assets_valor}, soma das subchaves é {soma_subchaves}")
    else:
        print(f"Erro de validação: TOTALASSETS = {total_assets_valor}, mas a soma das subchaves é {soma_subchaves}.")




#####################################################################
def buscar_balanco(ticker):
    try:
        empresa = yf.Ticker(ticker)
        balanco = empresa.balance_sheet.fillna(0)  # Substitui NaN por 0
        balanco.index = balanco.index.str.replace(' ', '')  # Remove espaços dos índices
        print(f"DataFrame do balanço para o ticker {ticker}:")
        print(balanco) 
        balanco.to_excel(f"{ticker}_BALANCO.xlsx")# Imprime o DataFrame para verificar se está correto
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
        cash.to_excel(f"{ticker}_CASH.xlsx")
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
        dre.to_excel(f"{ticker}_DRE.xlsx")
        # dre.to_excel(f"{ticker}_DRE.xlsx") # Imprime o DataFrame para verificar se está correto
        return dre
    except Exception as e:
        print(f"Erro ao buscar a Demonstração de Resultados para o ticker {ticker}: {e}")
        return None

def extrair_chaves(estrutura_json):
    chaves = set()

    def extrair(chave, estrutura):
        chaves.add(chave)
        if isinstance(estrutura, dict):
            for subchave, subestrutura in estrutura.items():
                extrair(subchave, subestrutura)

    for chave, estrutura in estrutura_json.items():
        extrair(chave, estrutura)

    return chaves

def processar_conta(df_balanco, conta, subcontas, ano, contas_nao_encontradas):
    conta_organizada = {}
    valor_conta = 0

    if conta in df_balanco.index:
        valor_conta = df_balanco.at[conta, ano]
    conta_organizada['valor'] = valor_conta if pd.notna(valor_conta) else 0

    soma_subcontas = 0
    for chave, subchaves in subcontas.items():
        if isinstance(subchaves, dict):
            subconta_organizada = processar_conta(df_balanco, chave, subchaves, ano, contas_nao_encontradas)
            soma_subcontas += subconta_organizada.get('valor', 0)
            conta_organizada[chave] = subconta_organizada
        else:
            valor_subconta = df_balanco.at[chave, ano] if chave in df_balanco.index else 0
            conta_organizada[chave] = valor_subconta if pd.notna(valor_subconta) else 0
            soma_subcontas += conta_organizada[chave]

    return conta_organizada

def organizar(df_balanco, estrutura_json):
    anos = df_balanco.columns
    balancos_por_ano = {}
    chaves_estrutura = extrair_chaves(estrutura_json)
    contas_nao_encontradas = set(df_balanco.index) - chaves_estrutura

    for ano in anos:
        balanco_organizado = {}
        for conta, subcontas in estrutura_json.items():
            balanco_organizado[conta] = processar_conta(df_balanco, conta, subcontas, ano, contas_nao_encontradas)
        balancos_por_ano[ano.strftime('%Y-%m-%d')] = balanco_organizado

    return balancos_por_ano, contas_nao_encontradas

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

    ticker = "SHCAY"
    df_balanco = buscar_balanco(ticker)
    df_cash_flow = buscar_fluxo_de_caixa(ticker)
    df_dre = buscar_dre(ticker)
    
    if df_balanco is None or df_cash_flow is None or df_dre is None:
        return

    balancos_organizados, contas_nao_encontradas_balanco = organizar(df_balanco, estrutura_json)
    cash_organizados, contas_nao_encontradas_cash = organizar(df_cash_flow, estrutura_json_cash)
    dre_organizados, contas_nao_encontradas_dre = organizar(df_dre, estrutura_json_dre)
    
    validar_coerencia(balancos_organizados, estrutura_json)
    validar_coerencia(cash_organizados, estrutura_json_cash)
    validar_coerencia(dre_organizados, estrutura_json_dre)
    
    for ano, balanco in balancos_organizados.items():
        try:
            with open(rf'C:\Users\gabri\Documents\projetos_python\Projeto_II\MAIN\FUNDAMENTALISTA\dados\Resultados\balanco_organizado_{ticker}_{ano}.json', 'w') as file:
                json.dump(balanco, file, indent=4)
        except Exception as e:
            print(f"Erro ao salvar o arquivo JSON para o ano {ano}: {e}")
    for ano, cash in cash_organizados.items():
        try:
            with open(rf'C:\Users\gabri\Documents\projetos_python\Projeto_II\MAIN\FUNDAMENTALISTA\dados\Resultados\cash_organizado_{ticker}_{ano}.json', 'w') as file:
                json.dump(cash, file, indent=4)
        except Exception as e:
            print(f"Erro ao salvar o arquivo JSON para o ano {ano}: {e}")
    for ano, dre in dre_organizados.items():
        try:
            with open(rf'C:\Users\gabri\Documents\projetos_python\Projeto_II\MAIN\FUNDAMENTALISTA\dados\Resultados\dre_organizado_{ticker}_{ano}.json', 'w') as file:
                json.dump(dre, file, indent=4)
        except Exception as e:
            print(f"Erro ao salvar o arquivo JSON para o ano {ano}: {e}")
            
    for ano, balanco in balancos_organizados.items():
        try:
            print()
            print()
            print('TESTE VALIDAÇÃO')
            caminho_arquivo =rf'C:\Users\gabri\Documents\projetos_python\Projeto_II\MAIN\FUNDAMENTALISTA\dados\Resultados\balanco_organizado_{ticker}_{ano}.json'
            with open(caminho_arquivo, 'r') as file:
                dados_json = json.load(file)
                validar_total_assets(dados_json)
        except Exception as e:
            print(f"Erro ao salvar o arquivo JSON para o ano {ano}: {e}")        
    

    # Printar as contas que estão no DataFrame mas não no JSON
    print()
    print("Contas no DataFrame, mas não no JSON do balanço:", contas_nao_encontradas_balanco)
    print()
    print()
    print("Contas no DataFrame, mas não no JSON do fluxo de caixa:", contas_nao_encontradas_cash)
    print()
    print()
    print("Contas no DataFrame, mas não no JSON da DRE:", contas_nao_encontradas_dre)
    print()
    print()

if __name__ == "__main__":
    main()

import yfinance as yf
import json
import pandas as pd
import time
from datetime import datetime, timedelta

pd.set_option("display.max_rows", None)

indicadores ={}
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

 # Função para adicionar um registro de indicador para um ativo em um determinado ano
def adicionar_indicador(ativo, ano, indicador, valor):
    # Converte o valor para float nativo do Python
    valor = float(valor)
    # Verifica se o ativo já existe no dicionário
    if ativo not in indicadores:
        # Se não existir, cria uma entrada para o ativo
        indicadores[ativo] = {}
    
    # Verifica se o indicador já existe para o ativo
    if indicador not in indicadores[ativo]:
        # Se não existir, cria uma entrada para o indicador
        indicadores[ativo][indicador] = {}
    
    # Adiciona ou atualiza o valor do indicador para o ano especificado
    indicadores[ativo][indicador][ano] = {"valor": valor}
 
def indicadores_fund(json_data, json_data_dre, ano, ticker ):
    ativo = yf.Ticker(ticker)
    
    # Converter a string 'ano' para um objeto datetime
    data_obj = datetime.strptime(ano, '%Y-%m-%d')
    
    # Subtrair 1 mês do objeto datetime, lidando com transições de mês e ano
    mes_ajustado_obj = data_obj.replace(day=1) - timedelta(days=1)
    mes_inicio = mes_ajustado_obj.strftime('%Y-%m-%d')
    
    # Obter o histórico do ativo
    historico = ativo.history(start=mes_inicio, end=ano)
     #Filtrar para pegar apenas as datas em que houve dividendos
    
    if ano in historico.index:
        preco_fechamento = historico.loc[ano, 'Close']
        print(f"Preço de fechamento em {ano}: {preco_fechamento}")
    else:
        ultimo_dia = historico.index[-1]
        preco_fechamento = historico.loc[ultimo_dia, 'Close']
        print(f"Preço de fechamento mais próximo em {ultimo_dia.date()}: {preco_fechamento}")
    
    #Para dividendos
    # Supondo que 'ano' seja uma string no formato 'YYYY-MM-DD'
    # Converter a string 'ano' para um objeto datetime
    data_obj = datetime.strptime(ano, '%Y-%m-%d')

    # Ajustar a data para o primeiro dia do ano
    ano_inicio = data_obj.replace(month=1, day=1)

    # Formatar a nova data como 'Ano-01-01'
    ano_inicio_str = ano_inicio.strftime('%Y-%m-%d')
    
    # obter histórico
    historico = ativo.history(start=ano_inicio_str, end=ano)
    # Filtrar apenas as colunas que têm informações de dividendos
    dividendos_historico = historico[historico['Dividends'] > 0]
    dividendos_historico = dividendos_historico['Dividends']
    
    # Total pago em dividendos
    total_dividendos = dividendos_historico.sum()

    # Dividendos pagos por ação
    # Assumindo que o valor já é por ação, então é o próprio valor que já temos.
    dividendos_por_acao = dividendos_historico

    # Dividendos pagos por ano
    dividendos_por_ano = dividendos_historico.groupby(dividendos_historico.index.year).sum()
    dividendos_pagos = dividendos_por_ano.iloc[0]
    # Exibindo os resultados
    print(f"Total pago em dividendos: {total_dividendos}")
    adicionar_indicador(ticker, ano,'Total pago em dividendos:', total_dividendos)
    print("Dividendos pagos por ação (por data):")
    print(dividendos_por_acao)
    print("Dividendos pagos por ano:")
    print(dividendos_pagos)
    adicionar_indicador(ticker, ano,'Dividendos pagos por ano:', dividendos_pagos)
    print(dividendos_historico)
    
    

    # Pegar os dividendos
    dividends = ativo.dividends

    # Converter para DataFrame e adicionar uma coluna com o ano
    dividends_df = dividends.to_frame()
    dividends_df['Year'] = dividends_df.index.year

    # Ordenar os dados pelo ano
    n_acoes = json_data['EXTRAS']["ORDINARYSHARESNUMBER"]["valor"]    
    dividendos_ano = n_acoes * dividendos_pagos
    # Exibir os resultados (ano e valor do dividendo)
    print(dividendos_ano)
    
    
    #
    print("Começando os indicadores Fundamentalistas em 30 segundos...")
    print() 
    
    print()
    liquidez_corrente = 0
    total_assets_valor = json_data["TOTALASSETS"]["valor"]
   # print(total_assets_valor)
    current_assets = json_data["TOTALASSETS"]["CURRENTASSETS"]["valor"]
    #print(current_assets)
    liabilities = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["CURRENTLIABILITIES"]["valor"]
    #print(liabilities)
    liquidez_corrente = current_assets / liabilities
    print(f'{liquidez_corrente} é o resultado do calculo para saber a capacidade da empresa cumprir suas obrigações a curto prazo.')
    
    adicionar_indicador(ticker, ano,'liquidez corrente', liquidez_corrente)
    print()
    print('ESTEJA ATENTO')
    print('<<< VOCÊ TERÁ 3 SEGUNDOS ENTRE UM INDICADOR E OUTRO >>> ')
    print()
    
    liquidez_imediata = 0
    caixa_e_equivalentes = json_data["TOTALASSETS"]["CURRENTASSETS"]['CASHCASHEQUIVALENTSANDSHORTTERMINVESTMENTS']['CASHANDCASHEQUIVALENTS']['valor']
    #print(caixa_e_equivalentes)
    passivo_circulante = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["CURRENTLIABILITIES"]["valor"]
    #print(passivo_circulante)
    liquidez_imediata = caixa_e_equivalentes / passivo_circulante
    print(f'{liquidez_imediata} É a capacidade da empresa cumprir suas obrigações a curto prazo sem perda de valor')
    print()
    adicionar_indicador(ticker, ano,'liquidez imediata', liquidez_imediata)
    print()
    
    liquidez_seca = 0
    current_assets = json_data["TOTALASSETS"]["CURRENTASSETS"]["valor"]
    #print(current_assets)
    inventory = json_data["TOTALASSETS"]["CURRENTASSETS"]['INVENTORY']["valor"]
    #print(inventory)
    liabilities = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["CURRENTLIABILITIES"]["valor"]
    #print(liabilities)
    liquidez_seca = (current_assets - inventory) / liabilities
    print(f'{liquidez_seca} Capacidade de cumprir suas obrigações considerando perda de estoque.')
    print()
    adicionar_indicador(ticker, ano,'liquidez seca', liquidez_seca)
    print()
    
    liquidez_geral = 0
    current_assets = json_data["TOTALASSETS"]["CURRENTASSETS"]["valor"]
    #print(current_assets)
    nom_current_assets = json_data["TOTALASSETS"]["TOTALNONCURRENTASSETS"]["valor"]
    #print(nom_current_assets)
    liabilities = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["CURRENTLIABILITIES"]["valor"]
    #print(liabilities)
    total_non_current_liabilities = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["TOTALNONCURRENTLIABILITIESNETMINORITYINTEREST"]["valor"]
    #print(total_non_current_liabilities)
    liquidez_geral = (current_assets + nom_current_assets) / (liabilities + total_non_current_liabilities)
    print(f'{liquidez_geral} Representa sua liquidez operacional. Capacidade da empresa de cumprir com todas as suas obrigações')
    print()
    adicionar_indicador(ticker, ano,'liquidez geral', liquidez_geral)
    print()
    
    
    print('1')
    print('2')
    print('3')
    print('indiozinhos')
    print('ENTRANDO EM COMPOSIÇÃO DOS ATIVOS...')
    print('Mais 3 segundos...')
    
    print()
    circulante = 0
    current_assets = json_data["TOTALASSETS"]["CURRENTASSETS"]["valor"]
    #print(current_assets)
    total_assets = json_data["TOTALASSETS"]["valor"]
    #print(total_assets)
    circulante = (current_assets ) / (total_assets)
    print(f'{circulante} Despesas operacionais e obrigações a curto prazo')
    print()
    adicionar_indicador(ticker, ano,'Ativos Circulantes', circulante)
    print()
    
    fixo = 0
    netppe = json_data["TOTALASSETS"]["TOTALNONCURRENTASSETS"]['NETPPE']["valor"]
    #print(netppe)
    investment_advances = json_data["TOTALASSETS"]["TOTALNONCURRENTASSETS"]['INVESTMENTSANDADVANCES']["valor"]
    #print(investment_advances)
    total_assets = json_data["TOTALASSETS"]["valor"]
    #print(total_assets)
    fixo = (netppe + investment_advances ) / (total_assets)
    print(f'{fixo} Representa os imobilizados por mais de ano, podem ser usados para gerar receita e para manter o funcionamento do negócio.')
    print()
    adicionar_indicador(ticker, ano,'Ativos Fixo', fixo)
    print()
    
    
    intangivel = 0
    goodwill = json_data["TOTALASSETS"]["TOTALNONCURRENTASSETS"]['GOODWILLANDOTHERINTANGIBLEASSETS']['GOODWILL']["valor"]
    #print(goodwill)
    other_intangibles = json_data["TOTALASSETS"]["TOTALNONCURRENTASSETS"]['GOODWILLANDOTHERINTANGIBLEASSETS']['OTHERINTANGIBLEASSETS']["valor"]
    #print(other_intangibles)
    total_assets = json_data["TOTALASSETS"]["valor"]
    #print(total_assets)
    intangivel = (goodwill + other_intangibles ) / (total_assets)
    print(f'{intangivel} Capacidade de gerar valor ao longo do tempo')
    print()
    adicionar_indicador(ticker, ano,'Ativos Intangivel', intangivel)
    print()
    
    investimento = 0
    Investment_and_advances = json_data["TOTALASSETS"]["TOTALNONCURRENTASSETS"]['INVESTMENTSANDADVANCES']["valor"]
    #print(goodwill)
    total_assets = json_data["TOTALASSETS"]["valor"]
    #print(Investment_and_advances)
    investimento = (Investment_and_advances ) / (total_assets)
    print(f'{investimento} investimentos')
    adicionar_indicador(ticker, ano,'Investimentos', investimento)
    print()
    
    # Calcular depreciação dos Ativos Fixos e outras Provisões 120  / (vida util do bem)
    # DEPRECIAÇÂO ATIVO FIXO  é uma despesa não monetária que reflete a redução do valor de um ativo fixo ao longo do tempo devido ao desgaste, obsolescência ou uso. Durante seu período útil
    #  é geralmente registrada no Demonstrativo de Resultados como uma despesa operacional e também afeta o valor contábil do ativo no Balanço Patrimonial.
    # Para Calcular BP ( CUSTO DO ATIVO - VALOR RESIDUAL / PELA VIDA ÙTIL DO ATIVO)
    custo_do_ativo =  json_data["TOTALASSETS"]["TOTALNONCURRENTASSETS"]["NETPPE"]["GROSSPPE"]["valor"]
    depreciacao_ativofixos_anual = (custo_do_ativo - netppe) / 120
    print(f'{depreciacao_ativofixos_anual} Representa a depreciação dos ativos fixos que reflete a redução do valor de um ativo fixo ao longo do tempo devido ao desgaste, obsolescência ou uso.')
    print()
    adicionar_indicador(ticker, ano,'Depreciação Ativos Fixos Anual', depreciacao_ativofixos_anual)
    print()
    
    # ÌNDICE DE ENDIVIDAMENTO é representada pela relação entre dívida e patrimônio líquido. refere-se ao uso de dívida para financiar as operações e investimentos de uma empresa
    # É importante ressaltar que a alavancagem financeira pode ser uma faca de dois gumes. Enquanto pode aumentar os retornos potenciais para os acionistas, também aumenta a exposição ao risco financeiro.
    # É fundamental avaliar como a empresa está utilizando a alavancagem e avaliar os riscos associados a ela
    # Para Calcular  BP (DÍVIDA TOTAL / PATRIMÔNIO LÍQUIDO)
    divida_total = json_data["EXTRAS"]["TOTALDEBT"]["valor"]
    patrimonio_liquido = json_data['TOTALEQUITYGROSSMINORITYINTEREST']['STOCKHOLDERSEQUITY']['valor']
    endividamento =  divida_total / patrimonio_liquido
    print(f'{endividamento}É o indice de endividamento ÌNDICE DE ENDIVIDAMENTO é representada pela relação entre dívida e patrimônio líquido. refere-se ao uso de dívida para financiar as operações e investimentos de uma empresa. É importante ressaltar que a alavancagem financeira pode ser uma faca de dois gumes. Enquanto pode aumentar os retornos potenciais para os acionistas, também aumenta a exposição ao risco financeiro. É fundamental avaliar como a empresa está utilizando a alavancagem e avaliar os riscos associados a ela.')
    adicionar_indicador(ticker, ano,'Endividamento', endividamento)
    print()
    # ÍNDICE DE ENDIVIDAMENTO LÌQUIDO é representada pela relação entre dívida e patrimônio líquido. refere-se ao uso de dívida para financiar as operações e investimentos de uma empresa
    # É importante ressaltar que a alavancagem financeira pode ser uma faca de dois gumes. Enquanto pode aumentar os retornos potenciais para os acionistas, também aumenta a exposição ao risco financeiro.
    # É fundamental avaliar como a empresa está utilizando a alavancagem e avaliar os riscos associados a ela
    # Para CAlcular BP (DÍVIDA LÍQUIDA / PATRIMÔNIO LÍQUIDO)
    divida_liquida = json_data["EXTRAS"]["NETDEBT"]["valor"]
    endividamento_liquido = divida_liquida / patrimonio_liquido
    print(f'Endividamento líquido {endividamento_liquido}')
    adicionar_indicador(ticker, ano,'Endividamento Líquido',endividamento_liquido)
    print()
   
    # RAZÃO DÍVIDA CAPITAL PRÓPRIO   proporção da dívida total em relação ao capital próprio mais a dívida total
    # a razão dívida/capital próprio é usada para avaliar o nível de endividamento em relação ao capital próprio da empresa. 
    # Para Calcular BP (DÍVIDA TOTAL / PL + DÍVIDA TOTAL)
    razao_divida_pl = divida_total / (patrimonio_liquido + divida_total)
    print(f'RAZÃO DÍVIDA CAPITAL PRÓPRIO {razao_divida_pl}')
    print()
    adicionar_indicador(ticker, ano,'Razao Divida Capital Proprio',razao_divida_pl)
    print()

    # COBERTURA DE JUROS é uma métrica que indica a capacidade de uma empresa pagar seus custos de juros com seus ganhos antes de juros e impostos (EBIT).
    # é importante para os credores e investidores, pois ajuda a avaliar o risco de crédito e a capacidade da empresa de cumprir suas obrigações financeiras.
    # Para calcular DRE ( EBIT / DESPESAS COM JUROS)
    ebit = json_data_dre["EBIT"]["valor"]
    despesas_com_juros =json_data_dre["OPERATINGEXPENSE"]["OTHEROPERATINGEXPENSES"]["valor"]
    cobertura_juros =  (ebit) / (despesas_com_juros)
    print(f' COBERTURA DE JUROS {cobertura_juros}')
    adicionar_indicador(ticker, ano,'Cobertura de Juros',cobertura_juros)

    print()
    print()
    print('4')
    print('5')
    print('6')
    print('indiozinhos')
    print('ENTRANDO EM COMPOSIÇÃO DOS PASSIVOS...')
    
    print()
    
    passivo_circulante_calculado = 0 ### pode ser utilizado para auditar o valor declarado pela empresa
    payable_acrued_expenses = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["CURRENTLIABILITIES"]["PAYABLESANDACCRUEDEXPENSES"]["valor"]
    #print(payable_acrued_expenses)
    current_provisions = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["CURRENTLIABILITIES"]["CURRENTPROVISIONS"]["valor"]
    #print(current_provisions) 
    pensionand_others = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["CURRENTLIABILITIES"]["PENSIONANDOTHERPOSTRETIREMENTBENEFITPLANSCURRENT"]["valor"]
    #print(pensionand_others)
    current_dbt_and_capital = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["CURRENTLIABILITIES"]["CURRENTDEBTANDCAPITALLEASEOBLIGATION"]["valor"]
    #print(current_dbt_and_capital)
    other_liabilities = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["CURRENTLIABILITIES"]["OTHERCURRENTLIABILITIES"]["valor"]
    #print(other_liabilities)
    total_liabilities = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["valor"]
    #print(total_liabilities)
    passivo_circulante_calculado = (payable_acrued_expenses + current_provisions + pensionand_others + current_dbt_and_capital + other_liabilities) / (total_liabilities)
    print(f'{passivo_circulante_calculado} Representa o calculo do passivo circulante e Dividas a curto prazo')
    print()
    adicionar_indicador(ticker, ano,'Passivo Circulante Calculado',passivo_circulante_calculado)
    adicionar_indicador(ticker, ano,'Passivo Circulante Obtido',passivo_circulante)
    print()
    
  
    passivo_nao_circulante_calculado = 0 
    long_provisions = json_data["TOTALEQUITYGROSSMINORITYINTEREST"]["STOCKHOLDERSEQUITY"]["valor"]
    #print(long_provisions)
    long_capital_obligation = json_data["TOTALEQUITYGROSSMINORITYINTEREST"]["MINORITYINTEREST"]["valor"]
    #print(long_capital_obligation) 
    non_current_defered = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["TOTALNONCURRENTLIABILITIESNETMINORITYINTEREST"]["NONCURRENTDEFERREDLIABILITIES"]["valor"]
    #print(non_current_defered)
    other_payables_non_current = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["TOTALNONCURRENTLIABILITIESNETMINORITYINTEREST"]["TRADEANDOTHERPAYABLESNONCURRENT"]["valor"]
    #print(other_payables_non_current)
    emplye_benefit = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["TOTALNONCURRENTLIABILITIESNETMINORITYINTEREST"]["EMPLOYEEBENEFITS"]["valor"]
    #print(emplye_benefit)
    non_current_accrued_expenses = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["TOTALNONCURRENTLIABILITIESNETMINORITYINTEREST"]["NONCURRENTACCRUEDEXPENSES"]["valor"]
    #print(non_current_accrued_expenses)
    derivative_product_liabilities = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["TOTALNONCURRENTLIABILITIESNETMINORITYINTEREST"]["DERIVATIVEPRODUCTLIABILITIES"]["valor"]
    #print(derivative_product_liabilities)
    related_parties_non_current = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["TOTALNONCURRENTLIABILITIESNETMINORITYINTEREST"]["DUETORELATEDPARTIESNONCURRENT"]["valor"]
    #print(related_parties_non_current)
    other_non_current = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["TOTALNONCURRENTLIABILITIESNETMINORITYINTEREST"]["OTHERNONCURRENTLIABILITIES"]["valor"]
    #print(other_non_current)
    total_liabilities = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["valor"]
    #print(total_liabilities)
    passivo_nao_circulante_calculado = (long_provisions + long_capital_obligation + non_current_defered + other_payables_non_current + emplye_benefit + non_current_accrued_expenses + derivative_product_liabilities + related_parties_non_current + other_non_current) / (total_liabilities)
    print(f'{passivo_nao_circulante_calculado} Representa o calculo do passivo não circulante e Dividas a longo prazo')
    adicionar_indicador(ticker, ano,'Passivo Não Circulante Calculado',passivo_nao_circulante_calculado)
    
    
    
    patrimonio_liquido = 0 
    equity = json_data["TOTALEQUITYGROSSMINORITYINTEREST"]["STOCKHOLDERSEQUITY"]["valor"]
    #print(equity)
    other_equity = json_data["TOTALEQUITYGROSSMINORITYINTEREST"]["MINORITYINTEREST"]["valor"]
    #print(other_equity) 
    total_liabilities = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["valor"]
    #print(total_liabilities)
    patrimonio_liquido = (equity + other_equity) / (total_liabilities)
    print(f'{patrimonio_liquido} Representa o Patrimonio líquido')
    print('FINALIZOU, GRACIAS BYE BYE')
    print()
    adicionar_indicador(ticker, ano,'Patrimônio Líquido',patrimonio_liquido)
    
    
    # MESCLANDO DRE E BALANÇO PARA OBTER MAIS INDICADORES
    # ALAVANCAGEM FINANCEIRA  é uma medida comum de avaliação da capacidade de uma empresa de pagar sua dívida com seus ganhos operacionais.
    # Essa relação indica quantos períodos (geralmente em anos) seriam necessários para pagar toda a dívida da empresa com seu EBITDA. 
    # é importante também considerar outros fatores, como a capacidade de gerar fluxo de caixa livre e a qualidade dos ativos.
    # Para Calcular DRE (EBITDA / BP DIVÌDA TOTAL )

    divida_total = json_data["EXTRAS"]["TOTALDEBT"]["valor"]
    ebitida_normalizado = json_data_dre["NORMALIZEDEBITDA"]["valor"]
    alavancagem_finan = (ebitida_normalizado) /  (divida_total)
    print("DRE + BALANÇO")
    print("INDICADORES:")
    adicionar_indicador(ticker, ano,'Divida Total',divida_total)
    print()
    print(f"Alavancagem Financeira: {alavancagem_finan}, é uma medida comum de avaliação da capacidade de uma empresa de pagar sua dívida com seus ganhos operacionais. Essa relação indica quantos períodos (geralmente em anos) seriam necessários para pagar toda a dívida da empresa com seu EBITDA.")
    adicionar_indicador(ticker, ano,'Alavancagem Financeira',alavancagem_finan)
    print()
    
    
    # ALAVANCAGEM FINANCEIRA LÌQUIDA é uma medida comum de avaliação da capacidade de uma empresa de pagar sua dívida com seus ganhos operacionais.
    # Essa relação indica quantos períodos (geralmente em anos) seriam necessários para pagar toda a dívida da empresa com seu EBITDA. 
    # é importante também considerar outros fatores, como a capacidade de gerar fluxo de caixa livre e a qualidade dos ativos.
    # Para Calcular DRE (EBITDA / BP DIVÌDA LÌQUIDA )
   
    print('DIVIDA LIQUIDA:')
    print()
    divida_liquida = json_data["EXTRAS"]["NETDEBT"]["valor"]
    alavancagem_finanliquida = (ebitida_normalizado) /  (divida_liquida)
    print(f'ALAVANCAGEM FINANCEIRA LÌQUIDA em {alavancagem_finanliquida} é uma medida comum de avaliação da capacidade de uma empresa de pagar sua dívida com seus ganhos operacionais. Essa relação indica quantos períodos (geralmente em anos) seriam necessários para pagar toda a dívida da empresa com seu EBITDA. É importante também considerar outros fatores, como a capacidade de gerar fluxo de caixa livre e a qualidade dos ativos.')
    adicionar_indicador(ticker, ano,'Alavancagem Financeira Liquida',alavancagem_finanliquida)
    
    
    # DÍVIDA LÌQUIDA/ EBIT serve para analisar o índice de endividamento de uma empresa, dando a noção de em quanto tempo a empresa pagaria todas as suas dívidas, caso o lucro operacional e o endividamento permaneçam constantes.
    # Esse indicador representa a diferença entre o faturamento e o custo operacional da empresa, sem levar em conta despesas ou receitas financeiras.
    # Quando maior for o resultado do Dívida Líquida/EBIT , maior será o sinal a respeito do endividamento desta empresa.
    # A Dívida Líquida representa a soma dos empréstimos e financiamentos (passivos) de uma empresa, após a subtração do caixa e equivalentes de caixa da empresa.
    # Já um índice mais baixo indica uma boa gestão financeira e que não há um alto nível de endividamento por parte da empresa.
    # Para Calcular (DÍVIDA LÍQUIDA / EBIT)
    dv_ebit = (divida_liquida) / (ebit)
    print()
    print(dv_ebit)
    print()
    adicionar_indicador(ticker, ano,'Divida Liquida por EBIT',dv_ebit)
    # DÍVIDA LÍQUIDA / EBITDA serve para analisar o índice de endividamento de uma empresa. Seu resultado demonstra o número de anos que uma empresa levaria para pagar sua dívida líquida no cenário em que o EBITDA permanece constante.
    # O resultado da Dívida Líquida/EBITDA é considerado alto quando está entre 4x e 5x, sendo um sinal negativo para o investidor e para a própria empresa. 
    # Já um índice entre 1x a 2x, por sua vez, é considerado mais saudável financeiramente pelo mercado, indicando uma boa gestão financeira da empresa.
    # Para Calcular ( (DÍVIDA LÍQUIDA / EBITDA)
    ebitida = json_data_dre["EBITDA"]["valor"]

    print()
    dv_ebitda = (divida_liquida) / (ebitida)
    print(dv_ebitda)
    print()
    adicionar_indicador(ticker, ano,'Divida Liquida por EBITDA',dv_ebitda)

    # PATRIMÔNIO /ATIVOS é um indicador financeiro que mostra a relação dos ativos no patrimônio de uma empresa.A métrica Patrimônio/Ativos considera que, quanto menor a relação, mais débitos a empresa precisa fazer para financiar seus ativos.
    # Quanto mais próximo de 100%, significa que ela consegue financiar quase todos os seus ativos com patrimônio, ao invés de assumir dívidas.
    # Para Calcular ( PATRIMÔNIO LÍQUIDO TOTAL / ATIVOS TOTAIS)
    pl_total = json_data["TOTALEQUITYGROSSMINORITYINTEREST"]["STOCKHOLDERSEQUITY"]["valor"]
    print()
    patrimonio_ativos = (pl_total) / (total_assets)
    print(patrimonio_ativos)
    adicionar_indicador(ticker, ano,'Patrimonio em Ativos',patrimonio_ativos)
    print()

    # PASSIVOS/ATIVOS  é um índice de alavancagem que compara a relação entre os passivos e os ativos de uma empresa
    # é possível ter uma noção do balanço da empresa e compará-la com o de outras do mesmo setor de atuação.
    # mostra como uma companhia pode crescer ao longo do tempo. Esse índice demonstra ao investidor a quantidade de ativos que são financiados pelos débitos da empresa, e não seu patrimônio.
    # Índices acima de 1 indicam que a empresa possui mais passivos que ativos. Sendo assim, a companhia representa um alto risco financeiro,
    # Para Calcular( PASSIVOS TOTAIS / ATIVOS TOTAIS)
    passivos_totais = json_data["TOTALLIABILITIESNETMINORITYINTEREST"]["valor"]
    print()
    passivo_ativos = (passivos_totais) / (total_assets)
    print(passivo_ativos)
    adicionar_indicador(ticker, ano,'Passivo Ativos',passivo_ativos)
    print()

    print('começando os indicadores mais divertidos hahaha')
    
    # D.Y (DIVIDEND YIELD)  é o indicador que verifica a performance da organização mediante os proventos que foram pagos aos acionistas da empresa ao longo dos últimos 12 meses do ano.
    # Entender a relação entre os dividendos que a empresa distribuiu e o preço atual da ação da companhia. Ou seja, o indicador torna possível avaliar o retorno da ação de acordo com os seus proventos pagos
    # analisar apenas um indicador ou uma empresa pode formar uma noção distante da realidade, de maneira geral.
    # Para Calcular  DY = DIVIDENDOS POR AÇÃO / PREÇO DA AÇÃO * 100
    # Dividendos por ação (DY)
    d_y = (dividendos_pagos / preco_fechamento) * 100
    print(f'{d_y} é a performance da organização mediante os proventos que foram pagos aos acionistas da empresa ao longo dos últimos 12 meses do ano')
    
    adicionar_indicador(ticker, ano,'Dividends Yield',d_y)
    
    
    net_income = json_data_dre["NETINCOMECOMMONSTOCKHOLDERS"]["NETINCOME"]["valor"]
    comomstock = json_data["TOTALEQUITYGROSSMINORITYINTEREST"]["STOCKHOLDERSEQUITY"]["CAPITALSTOCK"]["COMMONSTOCK"]["valor"]
    lucro_por_acao =  net_income / comomstock
    print()
    print(f'Lucro por ação: {lucro_por_acao}')
    adicionar_indicador(ticker, ano,'Lucro por Ação',lucro_por_acao)
    print()
    #P/L (PREÇO / LUCRO)  indicador do otimismo ou pessimismo usado no mercado pelos investidores, além de contribuir na identificação de oportunidades financeiras. 
    # um indicador de quanto o mercado está disposto a pagar pelos ganhos de uma empresa. P/L alto pode indicar uma ação com preço acima de seu preço justo, também pode demonstrar que o mercado possui boas expectativas sobre a empresa analisada.
    # P/L baixo indica que existe uma baixa confiabilidade no negócio pelo mercado ou que sua ação representa uma oportunidade de investimento ainda não notada pelos investidores. 
    # Importante Assim, vale uma atenção especial em resultados de P/L negativo, pois, não necessariamente isso representa um problema.Por exemplo, existem empresas cujo P/L é negativo pelo fato de que os lucros estão sendo reinvestidos na expansão do negócio. Ou seja, no longo prazo, este pode ser um bom negócio, especialmente pelo potencial de crescimento
    # Para Calcular PREÇO DA AÇÃO / LUCRO POR AÇÃO
    # P/L (Preço / Lucro)
    
    p_l = preco_fechamento / (preco_fechamento * lucro_por_acao)
    print('Preço por lucro:')
    print(p_l)
    adicionar_indicador(ticker, ano,'Preço por Lucro',p_l)
    
    
    
    # P/VP (PREÇO / VALOR PATRIMONIAL)  é um indicador que informa se o valor de uma ação está relativamente cara ou barata.
# é considerado baixo, com valor abaixo de 1, existe uma indicação de que a empresa vale menos do que seu patrimônio líquido dentro da bolsa. Para o investidor, isso pode representar uma boa oportunidade financeira, já que existe uma tendência de valorização posterior.
# resultado pode ser bastante variado, mas em períodos de crise, é comum que o P/VP esteja baixo devido às perspectivas negativas dos investidores. P/VP baixo pode indicar que existe alguma problema com aquele ativo, percebido pelo mercado. Por isso, é importante que haja uma análise mais ampla das informações e do contexto da empresa.
# Para Calcular (PREÇO / VALOR PATRIMONIAL) 
# P/VP (Preço / Valor Patrimonial)
    total_stock = json_data['TOTALEQUITYGROSSMINORITYINTEREST']['STOCKHOLDERSEQUITY']['valor']
    valor_patrimonial_por_acao = total_stock / comomstock
    
    print('preco fechamento:', preco_fechamento)
    print('preco stock total:', total_stock)
    print('preco stock commom:', comomstock)
    
    p_pv = preco_fechamento / valor_patrimonial_por_acao
    print(' P/VP (PREÇO / VALOR PATRIMONIAL)  é um indicador que informa se o valor de uma ação está relativamente cara ou barata. é considerado baixo, com valor abaixo de 1',  p_pv)
    adicionar_indicador(ticker, ano,'Preço por Valor Patrimonial',p_pv)
    
    
    
# EV / EBITDA é um importante indicador formado por dois indicadores bastante utilizados: EV e EBITDA. EV ( VALOR DA FIRMA) representa a soma entre o valor de mercado das ações de uma empresa e sua dívida líquida. Ele é formado por três componentes: Valor de Mercado, Valor das Dívidas e Caixa e Equivalentes de Caixa.
# EBITDA  (Lucro Antes de Juros, Impostos, Depreciação e Amortização – LAJIDA), representa o resultado operacional da empresa antes do desconto de:Juros,Impostos, Depreciação de bens e Amortização
# É comum que esse indicador seja útil em casos de fusões e aquisições, pois permite a comparação entre empresas com diferentes níveis de endividamento e até mesmo regimes tributários. Com o resultado, o investidor pode fazer análises ou comparações.
#  é preciso levar em conta a representação do EV, que é o valor atribuído à empresa pelo mercado. Se apenas esse indicador aumentar, é possível interpretar que a empresa está crescendo, mas produzindo o mesmo resultado.mercado possui perspectivas positivas, existe uma indicação de que o resultado operacional da empresa não evoluiu ao longo do tempo.
# Isso porque o EBITDA representa os resultados que a empresa obtém sem a subtração de suas despesas. No entanto, em uma situação onde apenas o EBITDA aumenta, o sinal é positivo, pois a empresa conseguiu melhores resultados mesmo sem apresentar um crescimento de tamanho e recursos
# Comparação entre empresas o resultado é considerado em anos, quanto mais baixo, menos tempo uma empresa leva para ter o retorno do seu investimento se mantiver a mesma produção operacional dos últimos 12 meses. No entanto, vale lembrar que, se esse resultado chegar através da diminuição do EV, existe a possibilidade de uma má reputação no mercado e problemas no caixa da empresa.
# Para Calcular   (EV = Capitalização + Dívida – Caixa e Equivalentes – Ativos Não-Operacionais / EBITDA = Resultado Operacional (DRE) + Depreciação + Amortização.)
 # EV/EBITDA
    cash = json_data["TOTALASSETS"]["CURRENTASSETS"]['CASHCASHEQUIVALENTSANDSHORTTERMINVESTMENTS']['CASHANDCASHEQUIVALENTS']['CASH']['valor']
    ev = (preco_fechamento * comomstock) + (total_liabilities - cash)
    ev_ebitda = ev / ebitida
    print('EV / EBITDA é um importante indicador formado por dois indicadores bastante utilizados: EV e EBITDA. EV ( VALOR DA FIRMA) representa a soma entre o valor de mercado das ações de uma empresa e sua dívida líquida. Ele é formado por três componentes: Valor de Mercado, Valor das Dívidas e Caixa e Equivalentes de Caixa. EBITDA  (Lucro Antes de Juros, Impostos, Depreciação e Amortização – LAJIDA), representa o resultado operacional da empresa antes do desconto de:Juros,Impostos, Depreciação de bens e Amortização É comum que esse indicador seja útil em casos de fusões e aquisições, pois permite a comparação entre empresas com diferentes níveis de endividamento e até mesmo regimes tributários. Com o resultado, o investidor pode fazer análises ou comparações.  é preciso levar em conta a representação do EV, que é o valor atribuído à empresa pelo mercado. Se apenas esse indicador aumentar, é possível interpretar que a empresa está crescendo, mas produzindo o mesmo resultado.mercado possui perspectivas positivas, existe uma indicação de que o resultado operacional da empresa não evoluiu ao longo do tempo. Isso porque o EBITDA representa os resultados que a empresa obtém sem a subtração de suas despesas. No entanto, em uma situação onde apenas o EBITDA aumenta, o sinal é positivo, pois a empresa conseguiu melhores resultados mesmo sem apresentar um crescimento de tamanho e recursos Comparação entre empresas o resultado é considerado em anos, quanto mais baixo, menos tempo uma empresa leva para ter o retorno do seu investimento se mantiver a mesma produção operacional dos últimos 12 meses. No entanto, vale lembrar que, se esse resultado chegar através da diminuição do EV, existe a possibilidade de uma má reputação no mercado e problemas no caixa da empresa.', ev_ebitda)
    adicionar_indicador(ticker, ano,'Valor da Firma por EBITDA',ev_ebitda)
    
# EV /EBIT é ajudar a identificar quanto uma empresa custa em relação ao que ela produz a partir de sua atividade fim.
# permite saber qual o potencial de geração de lucros de uma companhia. Vale lembrar que, para fins comparativos, ele deve ser utilizado apenas entre empresas do mesmo setor e, de preferência, que sejam concorrentes diretas.
# Quando o EV/EBIT está elevado, existe uma indicação de que a empresa possui uma boa avaliação no mercado. Consequentemente, isso significa que suas ações estão valorizadas.Enquanto isso, um EV/EBIT baixo demonstra que a empresa está sendo subavaliada. Com isso, possuem uma forte tendência de valorização ao longo do tempo, tornando a ação mais atrativa para a compra.
# Importante= O motivo para isso é que, por utilizar o EBIT, esse indicador não considera despesas ou receitas financeiras, nem mesmo gastos com impostos.Por isso, para uma análise eficiente, o EV/EBIT deve ser utilizado junto a outros índices financeiros.
# Para Calcular  (EV = Capitalização + Dívida – Caixa e Equivalentes – Ativos Não-Operacionais / EBIT Lucro Líquido + Resultado Financeiro + Impostos )
  # EV/EBIT
    ev_ebit = ev / ebit
    print('EV /EBIT é ajudar a identificar quanto uma empresa custa em relação ao que ela produz a partir de sua atividade fim. permite saber qual o potencial de geração de lucros de uma companhia. Vale lembrar que, para fins comparativos, ele deve ser utilizado apenas entre empresas do mesmo setor e, de preferência, que sejam concorrentes diretas. Quando o EV/EBIT está elevado, existe uma indicação de que a empresa possui uma boa avaliação no mercado. Consequentemente, isso significa que suas ações estão valorizadas.Enquanto isso, um EV/EBIT baixo demonstra que a empresa está sendo subavaliada. Com isso, possuem uma forte tendência de valorização ao longo do tempo, tornando a ação mais atrativa para a compra. Importante= O motivo para isso é que, por utilizar o EBIT, esse indicador não considera despesas ou receitas financeiras, nem mesmo gastos com impostos.Por isso, para uma análise eficiente, o EV/EBIT deve ser utilizado junto a outros índices financeiros.', ev_ebit)
    
    adicionar_indicador(ticker, ano,'Valor da Firma por EBIT',ev_ebit)

# PREÇO/EBITDA  é uma métrica que indica o potencial de geração de caixa de uma empresa. Esse indicador calcula a razão entre o preço da ação e o EBITDA da empresa por ação,  com cautela, já que o EBITDA de uma companhia nem sempre é direcionado para o seu caixa.
#  é relacionado com o total de ações negociadas pela companhia, podemos concluir que, quanto menor ele for, melhor. Isso porque ele indica que a empresa está depreciada em relação à sua geração de caixa, ou seja, que ela está mais barata em relação ao seu valor real.
#  Mesmo que uma empresa possua um alto EBITDA, o que realmente importa é a sua capacidade de transformação desse valor em caixa. Portanto, as despesas de uma companhia não podem ser muito elevadas, dependendo do volume do seu EBITDA.
# Para Calcular (P/EBITDA = PREÇO DA AÇÃO) / (EBITDA / QUANTIDADE DE AÇÕES )
# P/EBITDA
    p_ebitda = preco_fechamento / (ebitida / comomstock)
    print('PREÇO/EBITDA  é uma métrica que indica o potencial de geração de caixa de uma empresa. Esse indicador calcula a razão entre o preço da ação e o EBITDA da empresa por ação,  com cautela, já que o EBITDA de uma companhia nem sempre é direcionado para o seu caixa. é relacionado com o total de ações negociadas pela companhia, podemos concluir que, quanto menor ele for, melhor. Isso porque ele indica que a empresa está depreciada em relação à sua geração de caixa, ou seja, que ela está mais barata em relação ao seu valor real. Mesmo que uma empresa possua um alto EBITDA, o que realmente importa é a sua capacidade de transformação desse valor em caixa. Portanto, as despesas de uma companhia não podem ser muito elevadas, dependendo do volume do seu EBITDA.', p_ebitda)        
    adicionar_indicador(ticker, ano,'Preço por EBITDA',p_ebitda)
    

# PREÇO/EBIT  auxilia na avaliação do preço de ações de empresas. Por conta disso, ele costuma ser comparado com outros índices como o Lucro Líquido por Ação (LPA) e o Preço sobre Lucro (P/L),  a análise ocorre através da razão entre o preço da ação e o lucro operacional gerado pela empresa por ação.
#  o Indicador P/EBIT é uma boa métrica para a análise do preço de uma ação, desconsiderando lucros eventuais e de maneira inesperada, seja pela venda de ações ou outra medida não recorrente.
# permite entender se o preço das ações de uma empresa está dentro ou fora do esperado. Quando o resultado é menor do que o negociado, é possível perceber que o preço da ação está barato quando comparado ao lucro gerado para a empresa. Sendo assim, um bom momento para a compra desse ativo.
# onde o resultado é maior, significa que o preço da ação não está de acordo com o seu lucro gerado. Portanto, representando um melhor momento para a venda. É comum que o P/EBIT seja utilizado para fins comparativos entre empresas de um mesmo setor.
# Para Calcular (PREÇO DA AÇÃO) / (EBIT / QUANTIDADE DE AÇÕES)
# P/EBIT
    p_ebit = preco_fechamento / (ebit / comomstock)
    print('PREÇO/EBIT  auxilia na avaliação do preço de ações de empresas. Por conta disso, ele costuma ser comparado com outros índices como o Lucro Líquido por Ação (LPA) e o Preço sobre Lucro (P/L),  a análise ocorre através da razão entre o preço da ação e o lucro operacional gerado pela empresa por ação.  o Indicador P/EBIT é uma boa métrica para a análise do preço de uma ação, desconsiderando lucros eventuais e de maneira inesperada, seja pela venda de ações ou outra medida não recorrente. permite entender se o preço das ações de uma empresa está dentro ou fora do esperado. Quando o resultado é menor do que o negociado, é possível perceber que o preço da ação está barato quando comparado ao lucro gerado para a empresa. Sendo assim, um bom momento para a compra desse ativo. onde o resultado é maior, significa que o preço da ação não está de acordo com o seu lucro gerado. Portanto, representando um melhor momento para a venda. É comum que o P/EBIT seja utilizado para fins comparativos entre empresas de um mesmo setor.',  p_ebit)
    adicionar_indicador(ticker, ano,'Preço por EBIT',p_ebit)
    

# VPA é um índice bastante utilizado na comparação entre o valor de mercado e o valor patrimonial de uma determinado ativo.
# permite ao investidor a identificação de oportunidades de investimento, mas também de situações arriscadas.
# Através da comparação entre o preço de mercado e o valor real dentro da contabilidade da empresa, é possível que o valor oferecido dentro da bolsa seja maior que o VPA. Nesses casos, pode ser um indicativo de que o mercado está disposto a pagar mais pelas ações da empresa, que estão valorizadas
# Fatores determinantes como a oferta e procura, além de endividamento e histórico de prejuízos precisam ser levados em conta para uma avaliação realista de qualquer companhia. 
# Para Calcular ( PATRIMÔNIO LÌQUIDO / NÚMERO DE AÇÕES)
# VPA (Valor Patrimonial por Ação)
    vpa = valor_patrimonial_por_acao
    print('VPA é um índice bastante utilizado na comparação entre o valor de mercado e o valor patrimonial de uma determinado ativo. permite ao investidor a identificação de oportunidades de investimento, mas também de situações arriscadas. Através da comparação entre o preço de mercado e o valor real dentro da contabilidade da empresa, é possível que o valor oferecido dentro da bolsa seja maior que o VPA. Nesses casos, pode ser um indicativo de que o mercado está disposto a pagar mais pelas ações da empresa, que estão valorizadas Fatores determinantes como a oferta e procura, além de endividamento e histórico de prejuízos precisam ser levados em conta para uma avaliação realista de qualquer companhia.', vpa)
    adicionar_indicador(ticker, ano,'VPA',vpa)
    

# PREÇO / ATIVO é um indicador que mede a avaliação de mercado de uma empresa em relação ao seus ativos.
# é possível identificar o valor que o mercado financeiro atribui ao patrimônio de uma empresa em relação ao valor contábil do seu patrimônio. Essa informação é altamente relevante, já que o valor de mercado de uma ação reflete normalmente os fluxos de caixa futuros de uma companhia.
#  importante destacar que a avaliação do Preço sobre Total de Ativos deve ocorrer junto à do retorno sobre patrimônio líquido (ROE). Isso porque a discrepância entre esses dois índices costuma indicar uma supervalorização de ativos
# Para Calcular primeiro encontrar o VALOR CONTABIL POR AÇÃO = VALOR CONTABIL DA EMPRESA / TOTAL DE AÇÔES EM CIRCULAÇÃO) depois P/ATIVO = ( PREÇO DA AÇÃO / VALOR CONTÀBIL da AÇÃO)
 # P/Ativo
    valor_contabil_por_acao = total_assets / comomstock
    p_ativo = preco_fechamento / valor_contabil_por_acao
    print('PREÇO / ATIVO é um indicador que mede a avaliação de mercado de uma empresa em relação ao seus ativos. é possível identificar o valor que o mercado financeiro atribui ao patrimônio de uma empresa em relação ao valor contábil do seu patrimônio. Essa informação é altamente relevante, já que o valor de mercado de uma ação reflete normalmente os fluxos de caixa futuros de uma companhia.  importante destacar que a avaliação do Preço sobre Total de Ativos deve ocorrer junto à do retorno sobre patrimônio líquido (ROE). Isso porque a discrepância entre esses dois índices costuma indicar uma supervalorização de ativos',  p_ativo)
    adicionar_indicador(ticker, ano,'Preço por Ativo',p_ativo)
    

# LPA  pode ser utilizado como base para diversas métricas relevantes na análise de empresas, já que sua função principal é identificar o valor de lucro que uma companhia gera por cada ação que possui.
#  É importante que a análise desse indicador seja feita através do histórico da empresa. Isso porque uma análise única pode ser distorcida por fatores como lucros não recorrentes e alterações no volume de ações negociadas.
# Vale lembrar que, ainda que um LPA positivo indique a estabilidade financeira da empresa,
# Para Calcular (LUCRO LÍQUIDO / QUANIDADE DE AÇÕES)
    # LPA (Lucro por Ação)
    lpa = lucro_por_acao
    print('LPA  pode ser utilizado como base para diversas métricas relevantes na análise de empresas, já que sua função principal é identificar o valor de lucro que uma companhia gera por cada ação que possui.  É importante que a análise desse indicador seja feita através do histórico da empresa. Isso porque uma análise única pode ser distorcida por fatores como lucros não recorrentes e alterações no volume de ações negociadas. Vale lembrar que, ainda que um LPA positivo indique a estabilidade financeira da empresa,', lpa)
    adicionar_indicador(ticker, ano,'LPA',lpa)
    


# P/SR é uma métrica utilizada na análise fundamentalista para indicar o desempenho da receita líquida de uma companhia.
# compara o valor de mercado da empresa com sua Receita Operacional Líquida, e não com o Lucro Líquido
# para fins de comparação, é importante utilizá-lo com empresas semelhantes.
#  é possível concluir que empresas com índice menor que 1,0 conseguem gerar mais receita em comparação com seu valor de mercado. ESTUDAR MAIS
# Para Calcular (PREÇO DA AÇÃO / RECEITA LÍQUIDA POR AÇÃO) = RECEITA Líquida / Quantidade de ações )
# P/SR (Preço / Receita Líquida por Ação)
    total_revenue = json_data_dre['TOTALREVENUE']['valor']
    receita_liquida_por_acao = total_revenue / comomstock
    psr = preco_fechamento / receita_liquida_por_acao
    print('P/SR é uma métrica utilizada na análise fundamentalista para indicar o desempenho da receita líquida de uma companhia. compara o valor de mercado da empresa com sua Receita Operacional Líquida, e não com o Lucro Líquido para fins de comparação, é importante utilizá-lo com empresas semelhantes.  é possível concluir que empresas com índice menor que 1,0 conseguem gerar mais receita em comparação com seu valor de mercado. ESTUDAR MAIS',  psr)
    adicionar_indicador(ticker, ano,'P/SR Preço / Receita Líquida por Ação',psr)
    

# P/CAPITAL DE GIRO  aliada a outros indicadores, o P/Capital de Giro, que indicaria o valor ideal para se comprar o preço de um ativo de uma companhia na bolsa.
# é calculado por meio da divisão da cotação da ação no mercado e a quantidade de dinheiro que a empresa precisa para manter suas operações. ESTUDAR MAIS
# Para Calcular (PREÇO DA AÇÃO / CAPITAL DE GIRO POR AÇÃO) = ATIVO CIRCULANTE -PASSIVO CIRCULANTE / TOTAL DE AÇÕES EMITIDAS
# P/Capital de Giro
    total_current_liabilities = json_data['TOTALLIABILITIESNETMINORITYINTEREST']['CURRENTLIABILITIES']['valor']
    capital_giro_por_acao = (current_assets - total_current_liabilities) / comomstock
    p_capital_giro = preco_fechamento / capital_giro_por_acao
    print('P/CAPITAL DE GIRO  aliada a outros indicadores, o P/Capital de Giro, que indicaria o valor ideal para se comprar o preço de um ativo de uma companhia na bolsa. É calculado por meio da divisão da cotação da ação no mercado e a quantidade de dinheiro que a empresa precisa para manter suas operações. ESTUDAR MAIS',   p_capital_giro)
    adicionar_indicador(ticker, ano,'P/CAPITAL DE GIRO ',p_capital_giro)
    
    

# P/ATIVO CIRCULANTE LÍQUIDO é um indicador importante por identificar o valor que o mercado financeiro atribui ao patrimônio de uma empresa em relação ao seu valor disponível em caixa.
# Essa informação é relevante, já que o Ativo Circulante Líquido reflete a saúde financeira e a solidez da companhia em relação à emergências ou situações inesperadas.
# Sendo assim, um índice alto poderia ser entendido como a indicação de um bom fluxo de caixa. No entanto, vale ressaltar a importância de analisar outros índices na avaliação de uma empresa, e não somente este, de forma isolada.
#  para análises comparativas entre empresas de diferentes setores, ele não é o mais adequado.  não leva em consideração os diferentes padrões contábeis aplicados pelas companhias.  cenários imprevistos, como aquisições recentes e recompra de ações, que podem acabar distorcendo o resultado.
# Para calcular ( PREÇO DA AÇÃO / ATIVOS CIRCULANTES LÍQUIDOS POR AÇÃO) = Ativo Circulante Total /  total pelo número de ações
        # P/Ativo Circulante Líquido
    ativo_circulante_liquido_por_acao = current_assets / comomstock
    p_ativo_circulante_liquido = preco_fechamento / ativo_circulante_liquido_por_acao
    print('P/ATIVO CIRCULANTE LÍQUIDO é um indicador importante por identificar o valor que o mercado financeiro atribui ao patrimônio de uma empresa em relação ao seu valor disponível em caixa. Essa informação é relevante, já que o Ativo Circulante Líquido reflete a saúde financeira e a solidez da companhia em relação à emergências ou situações inesperadas. Sendo assim, um índice alto poderia ser entendido como a indicação de um bom fluxo de caixa. No entanto, vale ressaltar a importância de analisar outros índices na avaliação de uma empresa, e não somente este, de forma isolada.  para análises comparativas entre empresas de diferentes setores, ele não é o mais adequado.  não leva em consideração os diferentes padrões contábeis aplicados pelas companhias.  cenários imprevistos, como aquisições recentes e recompra de ações, que podem acabar distorcendo o resultado.',  p_ativo_circulante_liquido)
    adicionar_indicador(ticker, ano,'P/ATIVO CIRCULANTE LÍQUIDO',p_ativo_circulante_liquido)
    
    print(indicadores)
    caminho_arquivo = rf'C:\Users\gabri\Documents\projetos_python\Projeto_II\MAIN\FUNDAMENTALISTA\dados\comparativos\{ticker}_Indicadores.json'
     # Abre o arquivo no modo 'w' (escrita), o que sobrescreve o arquivo se ele já existir
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        json.dump(indicadores, f, ensure_ascii=False, indent=4)
    
    print(f"Dicionário salvo em: {caminho_arquivo}")

#####################################################################

def buscar_balanco(ticker):
    try:
        empresa = yf.Ticker(ticker)
        balanco = empresa.balance_sheet.fillna(0)
  # Substitui NaN por 0
        balanco.index = balanco.index.str.replace(' ', '')  # Remove espaços dos índices
        balanco.index = balanco.index.str.upper()  # Converte índices para uppercase
        print(f"DataFrame do balanço para o ticker {ticker}:")
        print(balanco)
        breakpoint()
    #    balanco.to_excel(f"{ticker}_BALANCO.xlsx") # Salva o DataFrame para verificar se está correto
        # datas_list = balanco.columns.to_list()
        # datas_formatadas = [data.strftime('%Y-%m-%d') for data in datas_list]
        # print('Datas List')
        # print(datas_formatadas)
        # 
        return balanco
    except Exception as e:
        print(f"Erro ao buscar o balanço para o ticker {ticker}: {e}")
        return None

def buscar_fluxo_de_caixa(ticker):
    try:
        empresa = yf.Ticker(ticker)
        cash = empresa.cash_flow.fillna(0)  # Substitui NaN por 0
        cash.index = cash.index.str.replace(' ', '')  # Remove espaços dos índices
        cash.index = cash.index.str.upper()  # Converte índices para uppercase
        print(f"DataFrame do fluxo de caixa para o ticker {ticker}:")
        print(cash)
        breakpoint()
      #  cash.to_excel(f"{ticker}_CASH.xlsx")
        return cash
    except Exception as e:
        print(f"Erro ao buscar o fluxo de caixa para o ticker {ticker}: {e}")
        return None

def buscar_dre(ticker):
    try:
        empresa = yf.Ticker(ticker)
        dre = empresa.financials.fillna(0)  # Substitui NaN por 0
        dre.index = dre.index.str.replace(' ', '')  # Remove espaços dos índices
        dre.index = dre.index.str.upper()  # Converte índices para uppercase
        print(f"DataFrame da Demonstração de Resultados para o ticker {ticker}:")
        print(dre)
        breakpoint()
     #   dre.to_excel(f"{ticker}_DRE.xlsx")
        return dre
    except Exception as e:
        print(f"Erro ao buscar a Demonstração de Resultados para o ticker {ticker}: {e}")
        return None

def extrair_chaves(estrutura_json):
    chaves = set()

    def extrair(chave, estrutura):
        chaves.add(chave.upper())
        if isinstance(estrutura, dict):
            for subchave, subestrutura in estrutura.items():
                extrair(subchave, subestrutura)

    for chave, estrutura in estrutura_json.items():
        extrair(chave, estrutura)

    return chaves

def processar_conta(df_balanco, conta, subcontas, ano, contas_nao_encontradas):
    conta_organizada = {}
    valor_conta = 0
    balanco_index_upper = [index.upper() for index in df_balanco.index]
    
    # Verifica se a conta está no DataFrame e obtém o valor
    if conta.upper() in balanco_index_upper:
        valor_conta = df_balanco.at[conta.upper(), ano]

    # Condição para CASH
    elif conta.upper() == 'CASH':
        andequivalents = df_balanco.loc['CASHANDCASHEQUIVALENTS', ano] if 'CASHANDCASHEQUIVALENTS' in df_balanco.index and ano in df_balanco.columns else 0
        equivalents = df_balanco.loc['CASHEQUIVALENTS', ano] if 'CASHEQUIVALENTS' in df_balanco.index and ano in df_balanco.columns else 0
        valor_conta = andequivalents - equivalents

    # Condição para MINERALPROPERTIES
    elif conta.upper() == 'MINERALPROPERTIES':
        g_ppe = df_balanco.loc['GROSSPPE', ano] if 'GROSSPPE' in df_balanco.index and ano in df_balanco.columns else 0
        landaprovm = df_balanco.loc['LANDANDIMPROVEMENTS', ano] if 'LANDANDIMPROVEMENTS' in df_balanco.index and ano in df_balanco.columns else 0
        machinery = df_balanco.loc['MACHINERYFURNITUREEQUIPMENT', ano] if 'MACHINERYFURNITUREEQUIPMENT' in df_balanco.index and ano in df_balanco.columns else 0
        o_propt = df_balanco.loc['OTHERPROPERTIES', ano] if 'OTHERPROPERTIES' in df_balanco.index and ano in df_balanco.columns else 0
        const_prog = df_balanco.loc['CONSTRUCTIONINPROGRESS', ano] if 'CONSTRUCTIONINPROGRESS' in df_balanco.index and ano in df_balanco.columns else 0
        leases = df_balanco.loc['LEASES', ano] if 'LEASES' in df_balanco.index and ano in df_balanco.columns else 0

        valor_conta = g_ppe - (landaprovm + machinery + o_propt + const_prog + leases)

    # Condição para OPERATIONANDMAINTENANCE
    elif conta.upper() == 'OPERATIONANDMAINTENANCE':
        op_exp = df_balanco.loc['OPERATINGEXPENSE', ano] if 'OPERATINGEXPENSE' in df_balanco.index and ano in df_balanco.columns else 0
        sell_adms = df_balanco.loc['SELLINGGENERALANDADMINISTRATION', ano] if 'SELLINGGENERALANDADMINISTRATION' in df_balanco.index and ano in df_balanco.columns else 0
        res_dev = df_balanco.loc['RESEARCHANDDEVELOPMENT', ano] if 'RESEARCHANDDEVELOPMENT' in df_balanco.index and ano in df_balanco.columns else 0
        dep_amo = df_balanco.loc['DEPRECIATIONAMORTIZATIONDEPLETIONINCOMESTATEMENT', ano] if 'DEPRECIATIONAMORTIZATIONDEPLETIONINCOMESTATEMENT' in df_balanco.index and ano in df_balanco.columns else 0
        prov_act = df_balanco.loc['PROVISIONFORDOUBTFULACCOUNTS', ano] if 'PROVISIONFORDOUBTFULACCOUNTS' in df_balanco.index and ano in df_balanco.columns else 0
        o_tax = df_balanco.loc['OTHERTAXES', ano] if 'OTHERTAXES' in df_balanco.index and ano in df_balanco.columns else 0
        o_tax_exp = df_balanco.loc['OTHEROPERATINGEXPENSES', ano] if 'OTHEROPERATINGEXPENSES' in df_balanco.index and ano in df_balanco.columns else 0

        valor_conta = op_exp - (res_dev + sell_adms + dep_amo + prov_act + o_tax + o_tax_exp)

    # print(valor_conta) # Use para debug se necessário

    
    conta_organizada['valor'] = valor_conta if pd.notna(valor_conta) else 0

    soma_subcontas = 0
    for chave, subchaves in subcontas.items():
        if isinstance(subchaves, dict):
            subconta_organizada = processar_conta(df_balanco, chave, subchaves, ano, contas_nao_encontradas)
            soma_subcontas += subconta_organizada.get('valor', 0)
            conta_organizada[chave.upper()] = subconta_organizada
        else:
            valor_subconta = df_balanco.at[chave.upper(), ano] if chave.upper() in df_balanco.index else 0
            conta_organizada[chave.upper()] = valor_subconta if pd.notna(valor_subconta) else 0
            soma_subcontas += conta_organizada[chave.upper()]

    return conta_organizada

def organizar(df_balanco, estrutura_json):
    anos = df_balanco.columns
    balancos_por_ano = {}
    chaves_estrutura = extrair_chaves(estrutura_json)
    contas_nao_encontradas = set(df_balanco.index.str.upper()) - chaves_estrutura

    for ano in anos:
        balanco_organizado = {}
        for conta, subcontas in estrutura_json.items():
            balanco_organizado[conta.upper()] = processar_conta(df_balanco, conta, subcontas, ano, contas_nao_encontradas)
        balancos_por_ano[ano.strftime('%Y-%m-%d')] = balanco_organizado

    return balancos_por_ano, contas_nao_encontradas

def validar_coerencia(balanco_organizado, estrutura_json):
    def validar_conta(conta_organizada, estrutura_json):
        for conta, valores in conta_organizada.items():
            if 'valor' in valores:
                subcontas = estrutura_json.get(conta.upper(), {})
                soma_subcontas = 0
                for subconta in subcontas:
                    if subconta.upper() != 'VALOR':
                        if isinstance(valores[subconta.upper()], dict):
                            soma_subcontas += valores[subconta.upper()].get('valor', 0) or 0
                        else:
                            soma_subcontas += valores.get(subconta.upper(), 0) or 0
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

    ticker = "ASAI3.SA"
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

    # Printar as contas que estão no DataFrame mas não no JSON
    print()
    print("Contas no DataFrame, mas não no JSON do balanço:", contas_nao_encontradas_balanco)
    print()
    print("Contas no DataFrame, mas não no JSON do fluxo de caixa:", contas_nao_encontradas_cash)
    print()
    print("Contas no DataFrame, mas não no JSON da DRE:", contas_nao_encontradas_dre)

    for ano, balanco in balancos_organizados.items():
        try:
            print()
            print()
            print('TESTE VALIDAÇÃO')
            caminho_arquivo = rf'C:\Users\gabri\Documents\projetos_python\Projeto_II\MAIN\FUNDAMENTALISTA\dados\Resultados\balanco_organizado_{ticker}_{ano}.json'
            caminho_arquivo_dre = rf'C:\Users\gabri\Documents\projetos_python\Projeto_II\MAIN\FUNDAMENTALISTA\dados\Resultados\dre_organizado_{ticker}_{ano}.json'
            caminho_arquivo_fluxo = rf'C:\Users\gabri\Documents\projetos_python\Projeto_II\MAIN\FUNDAMENTALISTA\dados\Resultados\cash_organizado_{ticker}_{ano}.json'
            
            # Verificar se o caminho do arquivo está correto
            print(f"Verificando arquivo: {caminho_arquivo}")
            
            with open(caminho_arquivo, 'r') as file:
                dados_json_balanco = json.load(file)
                
                # Verificar o conteúdo do JSON carregado
                # print(f"Conteúdo do JSON carregado: {dados_json_balanco}")
            with open(caminho_arquivo_dre, 'r') as file:
                dados_json_dre = json.load(file)
                
                # Verificar o conteúdo do JSON carregado
                print(f"Conteúdo do JSON carregado: {dados_json_balanco}")
                
                indicadores_fund(dados_json_balanco, dados_json_dre, ano, ticker)
                
        except FileNotFoundError:
            print(f"Arquivo não encontrado: {caminho_arquivo}")
        except json.JSONDecodeError:
            print(f"Erro ao decodificar o arquivo JSON: {caminho_arquivo}")
        except Exception as e:
            print(f"Erro ao processar o arquivo JSON para o ano {ano}: {e}") 
            
if __name__ == "__main__":
    main()

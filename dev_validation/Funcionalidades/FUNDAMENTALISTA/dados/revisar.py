import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd

# Definir o ticker da ação desejada
ticker = "CIEL3.SA"

# Criar um objeto Ticker para a empresa desejada (no exemplo, Petrobras)
petrobras = yf.Ticker(ticker)


# Configurar o Pandas para mostrar todas as linhas e colunas
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
valores = {}

# Obter dados financeiros
try:
    # Obter balanço patrimonial
    balance_sheet = petrobras.balance_sheet
    # Obter demonstração do fluxo de caixa
    cash_flow = petrobras.cashflow
    # Obter demonstração de resultados (DRE)
    income_statement = petrobras.financials

    # Exibir os dados do fluxo de caixa
    print("Demonstração do Fluxo de Caixa:")
    print(cash_flow)

    # Exibir os dados da Demonstração de Resultados (DRE):
    print("\nDemonstração de Resultados (DRE):")
    print(income_statement)

    print()
    print("Balanço Patrimonial:")
    print(balance_sheet)

    # Obter as datas do balanço patrimonial
    datas_balanco = balance_sheet.columns.tolist()
    datas_balanco_corrigido = []
    # Baixar dados históricos da ação
    historico = petrobras.history(period="5y")  # Baixar os últimos 5 anos de dados

    # Remover informações de fuso horário para evitar problemas de comparação
    historico.index = historico.index.tz_localize(None)

    # Filtrar os dados para as datas desejadas
    valores_desejados = {}
    for data in datas_balanco:
        data_disponivel = historico[:data].index.max()
        valor = historico.loc[data_disponivel, 'Close']
        valores_desejados[data_disponivel] = valor
        datas_balanco_corrigido.append(data_disponivel)

    # Exibir os valores das ações nas datas desejadas
    print("\nValores da PETR4.SA nas datas desejadas:")
    for data, valor in valores_desejados.items():
        print(f"Data: {data.date()} - Valor de Fechamento: R${valor:.2f}")
        valores[data] = valor

        # Obter dividendos pagos
    dividendos = petrobras.dividends
    dividendos_anuais = dividendos.resample('A').sum()

       # Exibir os dividendos anuais
    print("\nDividendos Anuais:")
    print(dividendos_anuais)


except Exception as e:
    print("Erro ao obter dados financeiros:", e)
    balance_sheet, cash_flow, income_statement = None, None, None

 # Filtrar os dados para as datas desejadas
    valores_desejados = {}
    for data in datas_balanco:
        data_disponivel = historico[:data].index.max()
        valor = historico.loc[data_disponivel, 'Close']
        valores_desejados[data] = valor

# Se os dados financeiros forem obtidos com sucesso, prosseguir com a análise
if balance_sheet is not None and cash_flow is not None and income_statement is not None:
    # Converter os dados em DataFrames do Pandas
    df_balance_sheet = pd.DataFrame(balance_sheet)
    df_cash_flow = pd.DataFrame(cash_flow)
    df_income_statement = pd.DataFrame(income_statement)

    # Realizar análise adicional, se necessário
    # ...
else:
    print("Não foi possível obter todos os dados financeiros.")

# Calcular Liquidez Corrente
# O índice de liquidez corrente é a capacidade de a empresa pagar suas obrigações de curto prazo, em outras palavras converter em dinheiro e utilizar no ciclo operacional dentro de um ano.
# um bom parametro é indices superior a 1 e se for muito maior analisar.
# é calculado buscando dados do balanço patrimonial (ATIVOS CIRCULANTES  / PASSIVOS CIRCULANTES)
liquidez_corrente = df_balance_sheet.loc['Current Assets'] / df_balance_sheet.loc['Current Liabilities']

# Calcular Liquidez Imediata
# O índice de líquidez imediata é o mais conservadora, pois indica a capacidade da empresa pagar suas obrigações de curto prazo usando apenas seus ativos mais líquidos sem perda significativa de valor
# Um bom paramêtro para interpretar é semelhante a o anterior próximo de 1 mostra que a empresa não precisa vender seu Estoque ()
# Para calcular BP  =  (Caixa e Equivalentes de Caixa  /  PASSIVOS CIRCULANTES)
liquidez_imediata = df_balance_sheet.loc['Cash And Cash Equivalents'] / df_balance_sheet.loc['Current Liabilities']

# Calcular Liquidez Seca
# O índice de líquidez seca é uma medida mais rigorosa, pois Exclui o seu estoque dos ativos circulantes sem perder valor
# Para calcular BP =  (ATIVOS CIRCULANTES - ESTOQUE  / PASSIVOS CIRCULANTES) 
liquidez_seca = (df_balance_sheet.loc['Current Assets'] - df_balance_sheet.loc['Inventory']) / df_balance_sheet.loc['Current Liabilities']

# Calcular Líquidez Geral
# O Índice de líquidez geral é a capacidade de uma empresa cumprir todas as obrigações de curto e longo prazo, utilizando ativos disponíveis
# quanto maior o índice melhor
# Calculada no BP =(ATIVO CIRCULANTE + ATIVOS NÂO CIRCULANTES  / PASSIVOS CIRCULANTES + PASSIVOS NÂO CIRCULANTES)
liquidez_geral = (df_balance_sheet.loc["Current Assets"] + df_balance_sheet.loc["Long Term Provisions"]) / (df_balance_sheet.loc["Current Liabilities"] + df_balance_sheet.loc["Total Non Current Liabilities Net Minority Interest"])


# Calcular a Composição do Ativo

# ATIVO CIRCULANTE é os recursos e direitos que a empresa tem que são esperados para serem convertidos em dinheiro ou consumidos no ciclo normal da empresa.
# È fundamental para as operações diarias , pois fornece recursos para cobrir suas obrigações de curto prazo e despesas operacionais.
# para Calcular BP = ( CAIXA E EQUIVALENTES DE CAIXA + CONTAS A RECEBER + ESTOQUES + APLICAÇÔES FINANCEIRAS + OUTROS ATIVOS CIRCULANTES / TOTAL DE ATIVOS )

# ATIVO FIXO é o imobilizado da empresa, são mantidos por mais de um ano na empresa e são essenciais para a geração de receita e funcionamento do négocio.
# é importante pois representa os investimentos da empresa em longo prazo, papel crucial na geração de receita e lucro.
# Para Calcular BP = ( IMÒVEIS + EQUIPAMENTOS + VEÌCULOS + MÒVEIS E UTENSÌLIOS + INVESTIMENTOS A LONGO PRAZO / TOTAL DE ATIVOS)

# ATIVO INTÀNGIVEL é ativos não físicos e não monetários que tem valor pelos direitos legais e econômicos associados.representam recursos valiosos na capacidade da empresa.
# São importantes para sua capacidade de gerar valor  ao longo do tempo, embora muito díficeis de serem mensurádos
# Para Calcular BP = (  GOODWILL + PATENTES + MARCAS E FRANQUIAS + DIREITOS AUTORAIS + SOFTWARES + CONTRATOS DE CLIENTES / TOTAL DE ATIVOS)

# INVESTIMENTOS é  onde a empresa tem ativos financeiros  com objetivo de gerar retorno futuro seja por meio de ganho de capital ou de recebimento de dividendos.
# São valiosos a valor justo de mercado, e quaisquer variações no valor justo são reconhecidas no resultado abrangente do período
# Para Calcular BP = ( INVESTIMENTOS EM AÇÔES + ATIVOS FINANCEIROS EM GERAL / TOTAL DE ATIVOS)

ativo_circulante = (df_balance_sheet.loc["Cash Cash Equivalents And Short Term Investments"] +  df_balance_sheet.loc["Receivables"] + df_balance_sheet.loc["Inventory"] +  df_balance_sheet.loc["Available For Sale Securities"]+  df_balance_sheet.loc["Other Current Assets"] ) / df_balance_sheet.loc["Total Assets"]
ativo_fixo = (df_balance_sheet.loc["Net PPE"]+ df_balance_sheet.loc["Investments And Advances"]) / (df_balance_sheet.loc["Total Assets"])
ativo_intangiveis = (df_balance_sheet.loc["Goodwill"] + df_balance_sheet.loc["Other Intangible Assets"] ) / (df_balance_sheet.loc["Total Assets"])
investimentos = (df_balance_sheet.loc["Investments And Advances"]) / (df_balance_sheet.loc["Total Assets"])

# GIRO DO ATIVO E ESTOQUE
# GIRO ATIVO  eficiência com que a empresa utiliza seus ativos para gerar receitas, ele mostra quantas vezes os ativos totais da empresa são convertidos em vendas no período.
# é importante para saber sua eficiência operacional, mas deve ser analisado com outros indicadores e com outras empresas do mesmo setor
# Para Calcular BP = ( VENDAS LÌQUIDAS / ATIVOS TOTAIS MÈDIOS DE PREFERENCIA  2 ANOS) nossso 4 anos
# GIRO ESTOQUE é o indicador da eficiência com que a empresa utiliza seus estoques para gerar vendas durante um período. ele mostra quantas vezes é substituido ao longo do tempo
# tem a mesma importância que o ativo referido a cima e deve ser interpretado da mesma forma para uma analise completa.
# Para Calcular BP = ( CUSTO DO PRODUTO VENDIDO / ESTOQUE MÈDIO)

# Verificar se os DataFrames não estão vazios
if not df_balance_sheet.empty and not df_income_statement.empty:
    # Selecionar apenas as colunas dos últimos quatro anos
    last_four_years_balance_sheet = df_balance_sheet.iloc[:, -4:]
    last_four_years_income_statement = df_income_statement.iloc[:, -4:]

    # Calcular o giro do ativo para cada ano
    giro_ativo = last_four_years_income_statement.loc["Total Revenue"] / last_four_years_balance_sheet.loc["Current Assets"]

    # Exibir o resultado para cada ano
    for year, giro in giro_ativo.items():
        print(f"Giro do Ativo em {year}: {giro}")

    # Calcular a média do giro do ativo dos últimos quatro anos
    media = giro_ativo.mean()

    # Exibir a média
    print("Média do giro do Ativo nos últimos quatro anos:", media)
else:
    print("DataFrame do balanço patrimonial ou do demonstrativo de resultados está vazio.")

# Verificar se os DataFrames não estão vazios
if not df_balance_sheet.empty and not df_income_statement.empty:
    # Selecionar apenas as colunas dos últimos quatro anos
    last_four_years_balance_sheet = df_balance_sheet.iloc[:, -4:]
    last_four_years_income_statement = df_income_statement.iloc[:, -4:]

    # Calcular o giro do estoque para cada ano
    giro_estoque = last_four_years_income_statement.loc["Reconciled Cost Of Revenue"] / ((last_four_years_balance_sheet.loc["Inventory"] + last_four_years_balance_sheet.loc["Inventory"].shift(-1)) / 2)

    # Exibir o resultado para cada ano
    for year, giro in giro_estoque.items():
        print(f"Giro do Estoque em {year}: {giro}")

    # Calcular a média do giro do estoque dos últimos quatro anos
    media = giro_estoque.mean()

    # Exibir a média
    print("Média do giro do Estoque nos últimos quatro anos:", media)
else:
    print("DataFrame do balanço patrimonial ou do demonstrativo de resultados está vazio.")

# Lucratividade ou EFICIÊNCIA

# MARGEM BRUTA indica a rentabilidade de vendas de uma empresa após a dedução do custo do produto vendido CPV 
# importante indicador de lucratividade mas deve ser avaliado com outros indicadores ou comparar com empresas do mesmo setor
# Para Calcular DRE = (LUCRO BRUTO / RECEITA TOTAL)

# MARGEM OPERACIONAL é um indicador financeiro que mede a eficiência operacional de uma empresa, ou seja, sua capacidade de gerar lucros em suas operações principal
# importante indicador de lucratividade na operação mas deve ser avaliado com outros indicadores ou comparar com empresas do mesmo setor
# Para CALCULAR DRE = ( LUCRO OPERACIONAL / RECEITA TOTAL)

# MARGEM EBITDA é um indicador financeiro que mede a lucratividade operacional de uma empresa antes de considerar os efeitos de juros, impostos, depreciação e amortização
# importante para avaliar a rentabilidade e eficiência  antes dos efeitos de juros, impostos, depreciação e amortização. mas deve ser avaliado com outros indicadores ou comparar com empresas do mesmo setor
# Para Calcular = DRE = (EBTIDA / RECEITA TOTAL)

# MARGEM EBIT  é um indicador que possibilita compreender e avaliar a eficiência operacional de uma empresa, 
# esse índice é utilizado para realizar comparativos da lucratividade operacionais de companhias de setores análogos.
#  possibilita que os impostos sejam excluídos, assim, proporciona um comparativo de companhias localizadas em diversos lugares.
#  quanto mais alta for a Margem EBIT de uma empresa, mais eficazes serão suas operações.
# Para Calcular  DRE = (EBIT / RECEITA TOTAL)


# MARGEM LUCRO LÌQUIDO é um indicador que mede a rentabilidade líquida em relação a receita total
# Um dos indicadores mais importantes para avaliar a rentabilidade e a saúde financeira da empresa, no entanto é importante considerar outros fatores, como contexto do setor e as tendências do mercado
# Para calcular  DRE = (LUCRO LÌQUIDO / RECEITA TOTAL)

margem_bruta = (df_income_statement.loc["Gross Profit"]) / (df_income_statement.loc["Total Revenue"])
margem_operacional = ( df_income_statement.loc["Operating Income"]) / (df_income_statement.loc["Total Revenue"])
margem_EBITDA = ( df_income_statement.loc["Normalized EBITDA"]) / (df_income_statement.loc["Total Revenue"])
margem_lucroliquido = ( df_income_statement.loc["Net Income"]) / ( df_income_statement.loc["Total Revenue"])
maegem_EBIT =  ( df_income_statement.loc["EBIT"]) / (df_income_statement.loc["Total Revenue"])

# Retorno sobre o Capital NOPAT Lucro Operacional * (1- taxa de impostos)

# RETORNO SOBRE O PL é um indicador que indica a efici~encia da empresa com que utiliza o capital dos acionistas para gerar lucro (ROE)
# é um potente indicador mas é  necessario comparar outros fatores, como estrutura de capital da empresa, natureza do negócio, condições econômicas além disso comparar o ROE com empresas do mesmo setor
# Para Calcular (DRE LUCRO LÌQUIDO / BP PATRIMONIO LÌQUIDO)
  
# RETORNO SOBRE OS ATIVOS  é um indicador financeiro que mede a eficiência com que uma empresa utiliza seus ativos para gerar lucro. (ROA)
# é um indicador importante para investidores e gestores, pois fornece insights sobre a eficiência operacional e a capacidade de geração de lucro de uma empresa. mas é  necessario comparar outros fatores, como estrutura de capital da empresa, natureza do negócio, condições econômicas além disso comparar o ROE com empresas do mesmo setor
# Para Calcular (DRE LUCRO LÌQUIDO / TOTAL ATIVOS)

# RETORNO DO CAPITAL INVESTIDO é um indicador financeiro que mede a eficiência com que uma empresa utiliza seu capital para gerar lucro. Ele mostra a capacidade de uma empresa de gerar lucro em relação ao capital total que emprega em suas operações.
# é um indicador importante para investidores e gestores, pois fornece insights sobre a eficiência operacional e a capacidade de geração de lucro de uma empresa. No entanto, é importante considerar outros fatores, como a estrutura de capital da empresa e as condições do mercado, ao interpretar o ROCE e compará-lo com outras empresas do mesmo setor.
# Para Calcular (DRE EBIT / BP TOTAL ATIVOS - PASSSIVOS CIRCULANTES)

# RETORNO CAPITAL INVESTIDO (ROIC) é que ele mostra o retorno percentual que a empresa está gerando para cada real investido em suas operações
# um ROIC positivo e crescente ao longo do tempo é um sinal positivo para os investidores, pois sugere que a empresa está sendo capaz de gerar lucro de forma consistente e eficiente com o capital que possui.
# Para Calcular (DRE = NOPAT / BP  Capital investido) =  ( Soma do capital dos acionistas com o capital de terceiros ) olhar

retorno_pl = ( df_income_statement.loc["Net Income"]) / ( df_balance_sheet.loc["Total Equity Gross Minority Interest"])
retorno_ativo = ( df_income_statement.loc["Net Income"]) / ( df_balance_sheet.loc["Total Assets"])
retorno_capitalempregado = ( df_income_statement.loc["EBIT"]) / (df_balance_sheet.loc["Total Assets"] - df_balance_sheet.loc["Current Liabilities"])
retorno_capitalinvestido =  ( df_income_statement.loc["Operating Income"] * 1 - df_income_statement.loc["Tax Rate For Calcs"]) / (df_balance_sheet.loc["Invested Capital"])


# Calcular a Composição do Passivo

# PASSIVO CIRCULANTE é uma parte importante do passivo total e consiste nas obrigações que a empresa espera liquidar dentro de um ano ou no ciclo operacional normal da empresa.
# Indica sua capacidade de cumprir suas obrigações de curto prazo com seus recursos circulantes, como caixa, estoque e contas a receber.
# Para Calcular BP ( FORNECEDORES + EMPRESTIMOS a CURTO PRAZO + OBRIGAÇÔES FISCAIS+ SALARIOS e ENCARGOS A PAGAR + OUTRAS DÌVIDAS DE CURTO PRAZO / TOTAL PASSIVO  )

# PASSSIVO NÂO CIRCULANTE é uma parte do passivo total de uma empresa que consiste em obrigações de longo prazo, ou seja, aquelas que não se espera que sejam liquidadas no curto prazo
# importantes para financiar investimentos de capital, expansão e outras atividades de longo prazo. Investidores e credores usam essa métrica para avaliar a estabilidade financeira e a capacidade de pagamento de longo prazo de uma empresa.
# Para calcular BP ( EMPRÈSTIMOS E FINANCIAMENTO A LONGO PRAZO + DEBÊNTURES + OBRIGAÇÔES FISCAIS DE LONGO PRAZO + PROVISÔES DE LONGO PRAZO + ARENDAMENTO FINANCEIRO E OUTRAS DÌVIDAS DE LONGO PRAZO / PASSIVO TOTAL)

# PATRIMÔNIO LÌQUIDO é uma das principais partes do balanço patrimonial de uma empresa e representa a diferença entre seus ativos e passivos. 
# É uma medida importante da saúde financeira e da solidez financeira de uma empresa
# Para Calcular BP ( CAPITAL SOCIAL + RESERVAS DE CAPITAL + LUCROS ACUMULADOS - PREJUÌZOS ACUMULADOS / PASSIVO TOTAL)

passivo_circulante = (df_balance_sheet.loc["Payables And Accrued Expenses"] + df_balance_sheet.loc["Current Provisions"] + df_balance_sheet.loc["Pensionand Other Post Retirement Benefit Plans Current"]  + df_balance_sheet.loc["Current Debt And Capital Lease Obligation"] + df_balance_sheet.loc["Other Current Liabilities"] ) / (df_balance_sheet.loc["Total Liabilities Net Minority Interest"])
passivo_naocirculante = (df_balance_sheet.loc["Long Term Provisions"] + df_balance_sheet.loc["Long Term Debt And Capital Lease Obligation"]+ df_balance_sheet.loc["Non Current Deferred Liabilities"] + df_balance_sheet.loc["Tradeand Other Payables Non Current"] + df_balance_sheet.loc["Employee Benefits"] + df_balance_sheet.loc["Other Non Current Liabilities"]) / (df_balance_sheet.loc["Total Liabilities Net Minority Interest"])
patrimonio_liquido = (df_balance_sheet.loc["Total Equity Gross Minority Interest"]) / (df_balance_sheet.loc["Total Liabilities Net Minority Interest"])

# ìndice de Alavancagem Financeira

# ALAVANCAGEM FINANCEIRA  é uma medida comum de avaliação da capacidade de uma empresa de pagar sua dívida com seus ganhos operacionais.
# Essa relação indica quantos períodos (geralmente em anos) seriam necessários para pagar toda a dívida da empresa com seu EBITDA. 
# é importante também considerar outros fatores, como a capacidade de gerar fluxo de caixa livre e a qualidade dos ativos.
# Para Calcular DRE (EBITDA / BP DIVÌDA TOTAL )

# ALAVANCAGEM FINANCEIRA LÌQUIDA é uma medida comum de avaliação da capacidade de uma empresa de pagar sua dívida com seus ganhos operacionais.
# Essa relação indica quantos períodos (geralmente em anos) seriam necessários para pagar toda a dívida da empresa com seu EBITDA. 
# é importante também considerar outros fatores, como a capacidade de gerar fluxo de caixa livre e a qualidade dos ativos.
# Para Calcular DRE (EBITDA / BP DIVÌDA LÌQUIDA )
alavancagem_finan = (df_income_statement.loc["Normalized EBITDA"]) /  (df_balance_sheet.loc["Total Debt"])
alavancagem_finanliquida = (df_income_statement.loc["Normalized EBITDA"]) /  (df_balance_sheet.loc["Net Debt"])

# Calcular depreciação dos Ativos Fixos e outras Provisões 120  / (vida util do bem)
# DEPRECIAÇÂO ATIVO FIXO  é uma despesa não monetária que reflete a redução do valor de um ativo fixo ao longo do tempo devido ao desgaste, obsolescência ou uso. Durante seu período útil
#  é geralmente registrada no Demonstrativo de Resultados como uma despesa operacional e também afeta o valor contábil do ativo no Balanço Patrimonial.
# Para Calcular BP ( CUSTO DO ATIVO - VALOR RESIDUAL / PELA VIDA ÙTIL DO ATIVO)

depreciacao_ativofixosanual = (df_balance_sheet.loc["Gross PPE"] - df_balance_sheet.loc["Net PPE"]) / 120

# Calculando a Análise da Estrutura de Capital:

# ÌNDICE DE ENDIVIDAMENTO é representada pela relação entre dívida e patrimônio líquido. refere-se ao uso de dívida para financiar as operações e investimentos de uma empresa
# É importante ressaltar que a alavancagem financeira pode ser uma faca de dois gumes. Enquanto pode aumentar os retornos potenciais para os acionistas, também aumenta a exposição ao risco financeiro.
# É fundamental avaliar como a empresa está utilizando a alavancagem e avaliar os riscos associados a ela
# Para Calcular  BP (DÍVIDA TOTAL / PATRIMÔNIO LÍQUIDO)

# ÍNDICE DE ENDIVIDAMENTO LÌQUIDO é representada pela relação entre dívida e patrimônio líquido. refere-se ao uso de dívida para financiar as operações e investimentos de uma empresa
# É importante ressaltar que a alavancagem financeira pode ser uma faca de dois gumes. Enquanto pode aumentar os retornos potenciais para os acionistas, também aumenta a exposição ao risco financeiro.
# É fundamental avaliar como a empresa está utilizando a alavancagem e avaliar os riscos associados a ela
# Para CAlcular BP (DÍVIDA LÍQUIDA / PATRIMÔNIO LÍQUIDO)

# RAZÃO DÍVIDA CAPITAL PRÓPRIO   proporção da dívida total em relação ao capital próprio mais a dívida total
# a razão dívida/capital próprio é usada para avaliar o nível de endividamento em relação ao capital próprio da empresa. 
# Para Calcular BP (DÍVIDA TOTAL / PL + DÍVIDA TOTAL)

# COBERTURA DE JUROS é uma métrica que indica a capacidade de uma empresa pagar seus custos de juros com seus ganhos antes de juros e impostos (EBIT).
# é importante para os credores e investidores, pois ajuda a avaliar o risco de crédito e a capacidade da empresa de cumprir suas obrigações financeiras.
# Para calcular DRE ( EBIT / DESPESAS COM JUROS)

# DÍVIDA LÌQUIDA/ EBIT serve para analisar o índice de endividamento de uma empresa, dando a noção de em quanto tempo a empresa pagaria todas as suas dívidas, caso o lucro operacional e o endividamento permaneçam constantes.
# Esse indicador representa a diferença entre o faturamento e o custo operacional da empresa, sem levar em conta despesas ou receitas financeiras.
# Quando maior for o resultado do Dívida Líquida/EBIT , maior será o sinal a respeito do endividamento desta empresa.
# A Dívida Líquida representa a soma dos empréstimos e financiamentos (passivos) de uma empresa, após a subtração do caixa e equivalentes de caixa da empresa.
# Já um índice mais baixo indica uma boa gestão financeira e que não há um alto nível de endividamento por parte da empresa.
# Para Calcular (DÍVIDA LÍQUIDA / EBIT)
dv_ebit = (df_balance_sheet.loc["Net Debt"]) / (df_income_statement.loc["EBIT"])

# DÍVIDA LÍQUIDA / EBITDA serve para analisar o índice de endividamento de uma empresa. Seu resultado demonstra o número de anos que uma empresa levaria para pagar sua dívida líquida no cenário em que o EBITDA permanece constante.
# O resultado da Dívida Líquida/EBITDA é considerado alto quando está entre 4x e 5x, sendo um sinal negativo para o investidor e para a própria empresa. 
# Já um índice entre 1x a 2x, por sua vez, é considerado mais saudável financeiramente pelo mercado, indicando uma boa gestão financeira da empresa.
# Para Calcular ( (DÍVIDA LÍQUIDA / EBITDA)
dv_ebitda = (df_balance_sheet.loc["Net Debt"]) / (df_income_statement.loc["EBITDA"])

# PATRIMÔNIO /ATIVOS é um indicador financeiro que mostra a relação dos ativos no patrimônio de uma empresa.A métrica Patrimônio/Ativos considera que, quanto menor a relação, mais débitos a empresa precisa fazer para financiar seus ativos.
# Quanto mais próximo de 100%, significa que ela consegue financiar quase todos os seus ativos com patrimônio, ao invés de assumir dívidas.
# Para Calcular ( PATRIMÔNIO LÍQUIDO TOTAL / ATIVOS TOTAIS)
patrimonio_ativos = (df_balance_sheet.loc["Stockholders Equity"]) / (df_balance_sheet.loc["Total Assets"])

# PASSIVOS/ATIVOS  é um índice de alavancagem que compara a relação entre os passivos e os ativos de uma empresa
# é possível ter uma noção do balanço da empresa e compará-la com o de outras do mesmo setor de atuação.
# mostra como uma companhia pode crescer ao longo do tempo. Esse índice demonstra ao investidor a quantidade de ativos que são financiados pelos débitos da empresa, e não seu patrimônio.
# Índices acima de 1 indicam que a empresa possui mais passivos que ativos. Sendo assim, a companhia representa um alto risco financeiro,
# Para Calcular( PASSIVOS TOTAIS / ATIVOS TOTAIS)
passivo_ativos = (df_balance_sheet.loc["Total Liabilities Net Minority Interest"]) / (df_balance_sheet.loc["Total Assets"])


indice_endividamento = (df_balance_sheet.loc["Total Debt"]) / (df_balance_sheet.loc["Stockholders Equity"])
indice_endividamento_liquido = (df_balance_sheet.loc["Net Debt"]) / (df_balance_sheet.loc["Stockholders Equity"])
razaodivida_capitalproprio = (df_balance_sheet.loc["Total Debt"]) / (df_balance_sheet.loc["Stockholders Equity"] + df_balance_sheet.loc["Total Debt"])
cobertura_juros =  (df_income_statement.loc["EBIT"]) / (df_income_statement.loc["Other Operating Expenses"])


# Política de Dividendos  # ver para puxar dvidendos ação e puxar o preço do dia  
dividendos_acao = (df_balance_sheet.loc["Dividends Payable"]) / (df_balance_sheet.loc["Share Issued"])
indice_pgdividendos = (df_balance_sheet.loc["Dividends Payable"]) / (df_balance_sheet.loc["Share Issued"]) / (df_income_statement.loc["Net Income"] / df_balance_sheet.loc["Share Issued"])


# Função para calcular os indicadores
def calcular_indicadores(df_balance_sheet, df_income_statement, dividendos_anuais, valores_desejados):
    indicadores = {}


    for data in df_balance_sheet.columns:
        try:
            # Valor de fechamento da ação na data
            preco_acao = valores_desejados[data]

# INDICADORES DE VALUATION




### BUSCAR PRECO ATUAL###########





 # D.Y (DIVIDEND YIELD)  é o indicador que verifica a performance da organização mediante os proventos que foram pagos aos acionistas da empresa ao longo dos últimos 12 meses do ano.
 # Entender a relação entre os dividendos que a empresa distribuiu e o preço atual da ação da companhia. Ou seja, o indicador torna possível avaliar o retorno da ação de acordo com os seus proventos pagos
 # analisar apenas um indicador ou uma empresa pode formar uma noção distante da realidade, de maneira geral.
 # Para Calcular  DY = DIVIDENDOS POR AÇÃO / PREÇO DA AÇÃO * 100
 # Dividendos por ação (DY)
            dividendos_por_acao = dividendos_anuais.loc[data.year, 'Dividends']
            d_y = (dividendos_por_acao / preco_acao) * 100
            indicadores[data] = {'DY': d_y}
       
 # P/L (PREÇO / LUCRO)  indicador do otimismo ou pessimismo usado no mercado pelos investidores, além de contribuir na identificação de oportunidades financeiras. 
 # um indicador de quanto o mercado está disposto a pagar pelos ganhos de uma empresa. P/L alto pode indicar uma ação com preço acima de seu preço justo, também pode demonstrar que o mercado possui boas expectativas sobre a empresa analisada.
 # P/L baixo indica que existe uma baixa confiabilidade no negócio pelo mercado ou que sua ação representa uma oportunidade de investimento ainda não notada pelos investidores. 
 # Importante Assim, vale uma atenção especial em resultados de P/L negativo, pois, não necessariamente isso representa um problema.Por exemplo, existem empresas cujo P/L é negativo pelo fato de que os lucros estão sendo reinvestidos na expansão do negócio. Ou seja, no longo prazo, este pode ser um bom negócio, especialmente pelo potencial de crescimento
 # Para Calcular PREÇO DA AÇÃO / LUCRO POR AÇÃO
# P/L (Preço / Lucro)
            lucro_por_acao = df_income_statement.loc['Net Income', data] / df_balance_sheet.loc['Common Stock', data]
            p_l = preco_acao / lucro_por_acao
            indicadores[data]['P/L'] = p_l

# P/VP (PREÇO / VALOR PATRIMONIAL)  é um indicador que informa se o valor de uma ação está relativamente cara ou barata.
# é considerado baixo, com valor abaixo de 1, existe uma indicação de que a empresa vale menos do que seu patrimônio líquido dentro da bolsa. Para o investidor, isso pode representar uma boa oportunidade financeira, já que existe uma tendência de valorização posterior.
# resultado pode ser bastante variado, mas em períodos de crise, é comum que o P/VP esteja baixo devido às perspectivas negativas dos investidores. P/VP baixo pode indicar que existe alguma problema com aquele ativo, percebido pelo mercado. Por isso, é importante que haja uma análise mais ampla das informações e do contexto da empresa.
# Para Calcular (PREÇO / VALOR PATRIMONIAL) 
# P/VP (Preço / Valor Patrimonial)
            valor_patrimonial_por_acao = df_balance_sheet.loc['Total Stockholder Equity', data] / df_balance_sheet.loc['Common Stock', data]
            p_pv = preco_acao / valor_patrimonial_por_acao
            indicadores[data]['P/VP'] = p_pv

# EV / EBITDA é um importante indicador formado por dois indicadores bastante utilizados: EV e EBITDA. EV ( VALOR DA FIRMA) representa a soma entre o valor de mercado das ações de uma empresa e sua dívida líquida. Ele é formado por três componentes: Valor de Mercado, Valor das Dívidas e Caixa e Equivalentes de Caixa.
# EBITDA  (Lucro Antes de Juros, Impostos, Depreciação e Amortização – LAJIDA), representa o resultado operacional da empresa antes do desconto de:Juros,Impostos, Depreciação de bens e Amortização
# É comum que esse indicador seja útil em casos de fusões e aquisições, pois permite a comparação entre empresas com diferentes níveis de endividamento e até mesmo regimes tributários. Com o resultado, o investidor pode fazer análises ou comparações.
#  é preciso levar em conta a representação do EV, que é o valor atribuído à empresa pelo mercado. Se apenas esse indicador aumentar, é possível interpretar que a empresa está crescendo, mas produzindo o mesmo resultado.mercado possui perspectivas positivas, existe uma indicação de que o resultado operacional da empresa não evoluiu ao longo do tempo.
# Isso porque o EBITDA representa os resultados que a empresa obtém sem a subtração de suas despesas. No entanto, em uma situação onde apenas o EBITDA aumenta, o sinal é positivo, pois a empresa conseguiu melhores resultados mesmo sem apresentar um crescimento de tamanho e recursos
# Comparação entre empresas o resultado é considerado em anos, quanto mais baixo, menos tempo uma empresa leva para ter o retorno do seu investimento se mantiver a mesma produção operacional dos últimos 12 meses. No entanto, vale lembrar que, se esse resultado chegar através da diminuição do EV, existe a possibilidade de uma má reputação no mercado e problemas no caixa da empresa.
# Para Calcular   (EV = Capitalização + Dívida – Caixa e Equivalentes – Ativos Não-Operacionais / EBITDA = Resultado Operacional (DRE) + Depreciação + Amortização.)
 # EV/EBITDA
            ev = (preco_acao * df_balance_sheet.loc['Common Stock', data]) + (df_balance_sheet.loc['Total Liabilities', data] - df_balance_sheet.loc['Cash', data])
            ebitda = df_income_statement.loc['EBITDA', data]
            ev_ebitda = ev / ebitda
            indicadores[data]['EV/EBITDA'] = ev_ebitda

# EV /EBIT é ajudar a identificar quanto uma empresa custa em relação ao que ela produz a partir de sua atividade fim.
# permite saber qual o potencial de geração de lucros de uma companhia. Vale lembrar que, para fins comparativos, ele deve ser utilizado apenas entre empresas do mesmo setor e, de preferência, que sejam concorrentes diretas.
# Quando o EV/EBIT está elevado, existe uma indicação de que a empresa possui uma boa avaliação no mercado. Consequentemente, isso significa que suas ações estão valorizadas.Enquanto isso, um EV/EBIT baixo demonstra que a empresa está sendo subavaliada. Com isso, possuem uma forte tendência de valorização ao longo do tempo, tornando a ação mais atrativa para a compra.
# Importante= O motivo para isso é que, por utilizar o EBIT, esse indicador não considera despesas ou receitas financeiras, nem mesmo gastos com impostos.Por isso, para uma análise eficiente, o EV/EBIT deve ser utilizado junto a outros índices financeiros.
# Para Calcular  (EV = Capitalização + Dívida – Caixa e Equivalentes – Ativos Não-Operacionais / EBIT Lucro Líquido + Resultado Financeiro + Impostos )
  # EV/EBIT
            ebit = df_income_statement.loc['EBIT', data]
            ev_ebit = ev / ebit
            indicadores[data]['EV/EBIT'] = ev_ebit

# PREÇO/EBITDA  é uma métrica que indica o potencial de geração de caixa de uma empresa. Esse indicador calcula a razão entre o preço da ação e o EBITDA da empresa por ação,  com cautela, já que o EBITDA de uma companhia nem sempre é direcionado para o seu caixa.
#  é relacionado com o total de ações negociadas pela companhia, podemos concluir que, quanto menor ele for, melhor. Isso porque ele indica que a empresa está depreciada em relação à sua geração de caixa, ou seja, que ela está mais barata em relação ao seu valor real.
#  Mesmo que uma empresa possua um alto EBITDA, o que realmente importa é a sua capacidade de transformação desse valor em caixa. Portanto, as despesas de uma companhia não podem ser muito elevadas, dependendo do volume do seu EBITDA.
# Para Calcular (P/EBITDA = PREÇO DA AÇÃO) / (EBITDA / QUANTIDADE DE AÇÕES )
# P/EBITDA
            p_ebitda = preco_acao / (ebitda / df_balance_sheet.loc['Common Stock', data])
            indicadores[data]['P/EBITDA'] = p_ebitda

# PREÇO/EBIT  auxilia na avaliação do preço de ações de empresas. Por conta disso, ele costuma ser comparado com outros índices como o Lucro Líquido por Ação (LPA) e o Preço sobre Lucro (P/L),  a análise ocorre através da razão entre o preço da ação e o lucro operacional gerado pela empresa por ação.
#  o Indicador P/EBIT é uma boa métrica para a análise do preço de uma ação, desconsiderando lucros eventuais e de maneira inesperada, seja pela venda de ações ou outra medida não recorrente.
# permite entender se o preço das ações de uma empresa está dentro ou fora do esperado. Quando o resultado é menor do que o negociado, é possível perceber que o preço da ação está barato quando comparado ao lucro gerado para a empresa. Sendo assim, um bom momento para a compra desse ativo.
# onde o resultado é maior, significa que o preço da ação não está de acordo com o seu lucro gerado. Portanto, representando um melhor momento para a venda. É comum que o P/EBIT seja utilizado para fins comparativos entre empresas de um mesmo setor.
# Para Calcular (PREÇO DA AÇÃO) / (EBIT / QUANTIDADE DE AÇÕES)
# P/EBIT
            p_ebit = preco_acao / (ebit / df_balance_sheet.loc['Common Stock', data])
            indicadores[data]['P/EBIT'] = p_ebit

# VPA é um índice bastante utilizado na comparação entre o valor de mercado e o valor patrimonial de uma determinado ativo.
# permite ao investidor a identificação de oportunidades de investimento, mas também de situações arriscadas.
# Através da comparação entre o preço de mercado e o valor real dentro da contabilidade da empresa, é possível que o valor oferecido dentro da bolsa seja maior que o VPA. Nesses casos, pode ser um indicativo de que o mercado está disposto a pagar mais pelas ações da empresa, que estão valorizadas
# Fatores determinantes como a oferta e procura, além de endividamento e histórico de prejuízos precisam ser levados em conta para uma avaliação realista de qualquer companhia. 
# Para Calcular ( PATRIMÔNIO LÌQUIDO / NÚMERO DE AÇÕES)
# VPA (Valor Patrimonial por Ação)
            vpa = valor_patrimonial_por_acao
            indicadores[data]['VPA'] = vpa

# PREÇO / ATIVO é um indicador que mede a avaliação de mercado de uma empresa em relação ao seus ativos.
# é possível identificar o valor que o mercado financeiro atribui ao patrimônio de uma empresa em relação ao valor contábil do seu patrimônio. Essa informação é altamente relevante, já que o valor de mercado de uma ação reflete normalmente os fluxos de caixa futuros de uma companhia.
#  importante destacar que a avaliação do Preço sobre Total de Ativos deve ocorrer junto à do retorno sobre patrimônio líquido (ROE). Isso porque a discrepância entre esses dois índices costuma indicar uma supervalorização de ativos
# Para Calcular primeiro encontrar o VALOR CONTABIL POR AÇÃO = VALOR CONTABIL DA EMPRESA / TOTAL DE AÇÔES EM CIRCULAÇÃO) depois P/ATIVO = ( PREÇO DA AÇÃO / VALOR CONTÀBIL da AÇÃO)
 # P/Ativo
            valor_contabil_por_acao = df_balance_sheet.loc['Total Assets', data] / df_balance_sheet.loc['Common Stock', data]
            p_ativo = preco_acao / valor_contabil_por_acao
            indicadores[data]['P/Ativo'] = p_ativo

# LPA  pode ser utilizado como base para diversas métricas relevantes na análise de empresas, já que sua função principal é identificar o valor de lucro que uma companhia gera por cada ação que possui.
#  É importante que a análise desse indicador seja feita através do histórico da empresa. Isso porque uma análise única pode ser distorcida por fatores como lucros não recorrentes e alterações no volume de ações negociadas.
# Vale lembrar que, ainda que um LPA positivo indique a estabilidade financeira da empresa,
# Para Calcular (LUCRO LÍQUIDO / QUANIDADE DE AÇÕES)
            # LPA (Lucro por Ação)
            lpa = lucro_por_acao
            indicadores[data]['LPA'] = lpa


# P/SR é uma métrica utilizada na análise fundamentalista para indicar o desempenho da receita líquida de uma companhia.
# compara o valor de mercado da empresa com sua Receita Operacional Líquida, e não com o Lucro Líquido
# para fins de comparação, é importante utilizá-lo com empresas semelhantes.
#  é possível concluir que empresas com índice menor que 1,0 conseguem gerar mais receita em comparação com seu valor de mercado. ESTUDAR MAIS
# Para Calcular (PREÇO DA AÇÃO / RECEITA LÍQUIDA POR AÇÃO) = RECEITA Líquida / Quantidade de ações )
# P/SR (Preço / Receita Líquida por Ação)
            receita_liquida_por_acao = df_income_statement.loc['Total Revenue', data] / df_balance_sheet.loc['Common Stock', data]
            psr = preco_acao / receita_liquida_por_acao
            indicadores[data]['P/SR'] = psr

# P/CAPITAL DE GIRO  aliada a outros indicadores, o P/Capital de Giro, que indicaria o valor ideal para se comprar o preço de um ativo de uma companhia na bolsa.
# é calculado por meio da divisão da cotação da ação no mercado e a quantidade de dinheiro que a empresa precisa para manter suas operações. ESTUDAR MAIS
# Para Calcular (PREÇO DA AÇÃO / CAPITAL DE GIRO POR AÇÃO) = ATIVO CIRCULANTE -PASSIVO CIRCULANTE / TOTAL DE AÇÕES EMITIDAS
# P/Capital de Giro
            capital_giro_por_acao = (df_balance_sheet.loc['Total Current Assets', data] - df_balance_sheet.loc['Total Current Liabilities', data]) / df_balance_sheet.loc['Common Stock', data]
            p_capital_giro = preco_acao / capital_giro_por_acao
            indicadores[data]['P/Capital de Giro'] = p_capital_giro

# P/ATIVO CIRCULANTE LÍQUIDO é um indicador importante por identificar o valor que o mercado financeiro atribui ao patrimônio de uma empresa em relação ao seu valor disponível em caixa.
# Essa informação é relevante, já que o Ativo Circulante Líquido reflete a saúde financeira e a solidez da companhia em relação à emergências ou situações inesperadas.
# Sendo assim, um índice alto poderia ser entendido como a indicação de um bom fluxo de caixa. No entanto, vale ressaltar a importância de analisar outros índices na avaliação de uma empresa, e não somente este, de forma isolada.
#  para análises comparativas entre empresas de diferentes setores, ele não é o mais adequado.  não leva em consideração os diferentes padrões contábeis aplicados pelas companhias.  cenários imprevistos, como aquisições recentes e recompra de ações, que podem acabar distorcendo o resultado.
# Para calcular ( PREÇO DA AÇÃO / ATIVOS CIRCULANTES LÍQUIDOS POR AÇÃO) = Ativo Circulante Total /  total pelo número de ações
        # P/Ativo Circulante Líquido
            ativo_circulante_liquido_por_acao = df_balance_sheet.loc['Total Current Assets', data] / df_balance_sheet.loc['Common Stock', data]
            p_ativo_circulante_liquido = preco_acao / ativo_circulante_liquido_por_acao
            indicadores[data]['P/Ativo Circulante Líquido'] = p_ativo_circulante_liquido

        except Exception as e:
            print(f"Erro ao calcular indicadores para a data {data}: {e}")
    return indicadores

# Se os dados financeiros forem obtidos com sucesso, prosseguir com a análise
if balance_sheet is not None and cash_flow is not None and income_statement is not None:
    # Converter os dados em DataFrames do Pandas
    df_balance_sheet = pd.DataFrame(balance_sheet)
    df_cash_flow = pd.DataFrame(cash_flow)
    df_income_statement = pd.DataFrame(income_statement)

    # Calcular os indicadores
    indicadores = calcular_indicadores(df_balance_sheet, df_income_statement, dividendos_anuais, valores_desejados)
    print("\nIndicadores de Valuation:")
    for data, indicador in indicadores.items():
        print(f"\nData: {data.date()}")
        for key, value in indicador.items():
            print(f"{key}: {value:.2f}")
else:
    print("Não foi possível obter todos os dados financeiros.")


# # Exibir os resultados
# liquidez_corrente = liquidez_corrente.dropna()
# liquidez_imediata = liquidez_imediata.dropna()
# liquidez_seca = liquidez_seca.dropna()
# liquidez_geral = liquidez_geral.dropna()
# ativo_circulante = ativo_circulante.dropna()
# ativo_fixo = ativo_fixo.dropna()
# ativo_intangiveis = ativo_intangiveis.dropna()
# investimentos = investimentos.dropna()
# depreciacao_ativofixosanual = depreciacao_ativofixosanual.dropna()
# indice_endividamento = indice_endividamento.dropna()
# indice_endividamento_liquido = indice_endividamento_liquido.dropna()
# alavancagem_finan = alavancagem_finan.dropna()
# razaodivida_capitalproprio = razaodivida_capitalproprio.dropna()
# passivo_circulante = passivo_circulante.dropna()
# cobertura_juros = cobertura_juros.dropna()
# passivo_naocirculante = passivo_naocirculante.dropna()
# patrimonio_liquido = patrimonio_liquido.dropna()
# margem_bruta = margem_bruta.dropna()
# margem_operacional = margem_operacional.dropna()
# margem_EBITDA = margem_EBITDA.dropna()
# margem_lucroliquido = margem_lucroliquido.dropna()
# retorno_pl = retorno_pl.dropna()
# retorno_ativo = retorno_ativo.dropna()
# retorno_capitalempregado = retorno_capitalempregado.dropna()
# retorno_capitalinvestido = retorno_capitalinvestido.dropna()
# dividendos_acao = dividendos_acao.dropna()
# indice_pgdividendos = indice_pgdividendos.dropna()
# dv_ebit = dv_ebit.dropna()
# dv_ebitda = dv_ebitda.dropna()
# patrimonio_ativos = patrimonio_ativos.dropna()
# passivo_ativos = passivo_ativos.dropna()
# dividendos_acao = dividendos_acao.dropna()
# lucro_por_acao = lucro_por_acao.dropna()

# print("Indicadores de Liquidez:")
# print("Liquidez Corrente:", liquidez_corrente)
# print("Liquidez Imediata:", liquidez_imediata)
# print("Liquidez Seca:", liquidez_seca)
# print("Líquidez Geral:",liquidez_geral)
# print("Ativo Circulante:", ativo_circulante)
# print("ativo_fixo:", ativo_fixo)
# print("ativo_intangíveis:", ativo_intangiveis)
# print("Investimentos:",investimentos)
# print("depreciacao_ativofixosanual:", depreciacao_ativofixosanual)
# print("indice de Endividamento:", indice_endividamento)
# print("ìndice de Alavancagem Financeira:", alavancagem_finan)
# print("Razão dívida e Capital Próprio:", razaodivida_capitalproprio)
# print("Cobertura de Juros:", cobertura_juros)
# print("Passivo não Circulante:", passivo_naocirculante)
# print(" Patrimônio Líquido:",patrimonio_liquido)
# print("Passivo Circulante:", passivo_circulante)
# print("Margem Bruta:",margem_bruta )
# print("Margem Operacional:", margem_operacional)
# print("Margem EBITDA:", margem_EBITDA)
# print("Margem de Lucro Líquido:", margem_lucroliquido)
# print("Retorno sobre o PL:", retorno_pl)
# print("Retorno sobre Ativos:", retorno_ativo)
# print("Retorno sobre o Capital Empregado:", retorno_capitalempregado)
# print("Retorno sobre o Capital Investido:", retorno_capitalinvestido)
# print("Dividendos por Ação:", dividendos_acao)
# print("ìndice de Pagamento de Dividendos:",indice_pgdividendos)
# print("lucro_por_acao;",lucro_por_acao)
# # Definir indicadores
indicadores = {
    "Liquidez Corrente": "liquidez_corrente",
    "Liquidez Imediata": "liquidez_imediata",
    "Liquidez Seca": "liquidez_seca",
    "Liquidez Geral": "liquidez_geral",
    "Ativo Circulante": "ativo_circulante",
    "Ativo Fixo": "ativo_fixo",
    "Ativo Intangível": "ativo_intangiveis",
    "Investimentos": "investimentos",
    "Depreciação do Ativo Fixo (Anual)": "depreciacao_ativofixosanual",
    "Índice de Endividamento": "indice_endividamento",
    "Índice de Alavancagem Financeira": "alavancagem_finan",
    "Razão Dívida e Capital Próprio": "razaodivida_capitalproprio",
    "Cobertura de Juros": "cobertura_juros",
    "Passivo Não Circulante": "passivo_naocirculante",
    "Patrimônio Líquido": "patrimonio_liquido",
    "Passivo Circulante": "passivo_circulante",
    "Margem Bruta": "margem_bruta",
    "Margem Operacional": "margem_operacional",
    "Margem EBITDA": "margem_EBITDA",
    "Margem de Lucro Líquido": "margem_lucroliquido",
    "Retorno sobre o Patrimônio Líquido": "retorno_pl",
    "Retorno sobre Ativos": "retorno_ativo",
    "Retorno sobre o Capital Empregado": "retorno_capitalempregado",
    "Retorno sobre o Capital Investido": "retorno_capitalinvestido",
    "Dividendos por Ação": "dividendos_acao",
    "Índice de Pagamento de Dividendos": "indice_pgdividendos"
}

# Função para plotar o gráfico do indicador selecionado
def plotar_grafico(indicador):
    plt.figure(figsize=(10, 6))
    plt.bar(df.index, df[indicador])
    plt.title(indicador)
    plt.xlabel('Data')
    plt.ylabel('Valor do Indicador')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Criar DataFrame com os valores dos indicadores
valores = {
    "liquidez_corrente": liquidez_corrente,
    "liquidez_imediata": liquidez_imediata,
    "liquidez_seca": liquidez_seca,
    "liquidez_geral": liquidez_geral,
    "ativo_circulante": ativo_circulante,
    "ativo_fixo": ativo_fixo,
    "ativo_intangiveis": ativo_intangiveis,
    "investimentos": investimentos,
    "depreciacao_ativofixosanual": depreciacao_ativofixosanual,
    "indice_endividamento": indice_endividamento,
    "alavancagem_finan": alavancagem_finan,
    "razaodivida_capitalproprio": razaodivida_capitalproprio,
    "cobertura_juros": cobertura_juros,
    "passivo_naocirculante": passivo_naocirculante,
    "patrimonio_liquido": patrimonio_liquido,
    "passivo_circulante": passivo_circulante,
    "margem_bruta": margem_bruta,
    "margem_operacional": margem_operacional,
    "margem_EBITDA": margem_EBITDA,
    "margem_lucroliquido": margem_lucroliquido,
    "retorno_pl": retorno_pl,
    "retorno_ativo": retorno_ativo,
    "retorno_capitalempregado": retorno_capitalempregado,
    "retorno_capitalinvestido": retorno_capitalinvestido,
    "dividendos_acao": dividendos_acao,
    "indice_pgdividendos": indice_pgdividendos
}
df = pd.DataFrame(valores)

# Interatividade para escolher o indicador
def interativo(indicador):
    plotar_grafico(indicador)

# Exibir lista de indicadores interativa
plt.figure(figsize=(15, 8))
plt.subplot(1, 2, 1)
plt.text(0.5, 0.5, "Selecione um indicador", ha='center', va='center', fontsize=15)
plt.axis('off')

plt.subplot(1, 2, 2)
plt.xticks(rotation=90)
plt.bar(indicadores.keys(), range(len(indicadores)))
plt.title('Indicadores')
plt.xlabel('Indicador')
plt.ylabel('Índice')

plt.tight_layout()
plt.show()
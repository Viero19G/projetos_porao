import yfinance as yf

# Definir o ticker da empresa (exemplo: Apple)
ticker = 'PETR4.SA'

# Baixar os dados da empresa usando yfinance
empresa = yf.Ticker(ticker)

# Obter o histórico de dividendos
dividendos = empresa.dividends

# Filtrar os dividendos apenas para o ano de 2021
dividendos_2021 = dividendos['2021-01-01':'2021-12-31']

# Somar os dividendos do ano de 2021
dividendos_total_2021 = dividendos_2021.sum()

# Mostrar os dividendos pagos em 2021
print(f"Dividendos pagos em 2021: {dividendos_total_2021}")
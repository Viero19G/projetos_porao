import json
import plotly.graph_objs as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
from datetime import datetime
import dash_bootstrap_components as dbc  # Componente de estilo bootstrap

# Carregar o JSON


# Função para extrair todos os indicadores do dicionário JSON
def extrair_indicadores(ativo):
    with open(fr'C:\Users\gabri\Documents\projetos_python\Projeto_II\MAIN\FUNDAMENTALISTA\dados\comparativos\{ativo}_Indicadores.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    return list(dados[ativo].keys()), dados


# Variáveis globais para temas
THEME_LIGHT = dbc.themes.BOOTSTRAP
THEME_DARK = dbc.themes.DARKLY

# Extrair automaticamente os indicadores do JSON
ativo = 'ASAI3.SA'  # Exemplo de ativo
indicadores_disponiveis, dados = extrair_indicadores(ativo)

# Inicializar o app com tema claro por padrão
app = Dash(__name__, external_stylesheets=[THEME_LIGHT])

# Layout do dashboard
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1('Dashboard Comparativo Financeiro', className='text-center mb-4'), width=10),
        dbc.Col(
            html.Div(
                id='theme-icon',
                children=[
                    html.I(className="bi bi-brightness-high", id="sol-lua-icon", style={'font-size': '24px', 'cursor': 'pointer'})
                ],
                className='text-right'
            ), width=2
        )
    ]),

    dbc.Row([dbc.Col(html.Div('Selecione os anos para comparação:'), width=12)]),

    dbc.Row([dbc.Col(
        dcc.Checklist(
            id='ano-checklist',
            options=[{'label': datetime.strptime(ano, '%Y-%m-%d').year, 'value': ano} for ano in dados[ativo][indicadores_disponiveis[0]]],
            value=['2020-12-31', '2023-12-31'],  # Anos padrão
            inline=True,
            className='mb-4'
        ), width=12)
    ]),

    dbc.Row([dbc.Col(html.Div('Selecione os indicadores:'), width=12)]),

    dbc.Row([dbc.Col(
        dcc.Dropdown(
            id='indicador-dropdown',
            options=[{'label': indicador, 'value': indicador} for indicador in indicadores_disponiveis],
            value=[indicadores_disponiveis[0]],  # Indicador padrão
            multi=True,
            className='mb-4'
        ), width=12)
    ]),

    # Div para os gráficos, com rolagem caso ultrapasse 9 gráficos (3x3)
    dbc.Row(id='graficos-comparativos', style={'max-height': '800px', 'overflow-y': 'auto'}),  # Altura máxima com scroll

    dbc.Row([dbc.Col(html.Div(id='diferenca-legenda', className='mt-4 text-center'), width=12)]),

    dcc.Store(id='theme-store', data={'theme': 'light'})  # Armazena o estado do tema
], fluid=True, id='main-container')

# Callback para alternar o ícone e o tema claro e escuro
@app.callback(
    [Output('theme-store', 'data'),
     Output('sol-lua-icon', 'className'),
     Output('main-container', 'style')],
    [Input('sol-lua-icon', 'n_clicks')],
    [State('theme-store', 'data')]
)
def alternar_tema(n_clicks, theme_data):
    if theme_data['theme'] == 'light':
        theme_data['theme'] = 'dark'
        icon_class = 'bi bi-moon'
        style = {'background-color': '#2c2c2c', 'color': '#ffffff'}
    else:
        theme_data['theme'] = 'light'
        icon_class = 'bi bi-brightness-high'
        style = {'background-color': '#ffffff', 'color': '#000000'}

    return theme_data, icon_class, style

# Callback para atualizar os gráficos e calcular as diferenças
@app.callback(
    [Output('graficos-comparativos', 'children'),
     Output('diferenca-legenda', 'children')],
    [Input('indicador-dropdown', 'value'),
     Input('ano-checklist', 'value')]
)
def atualizar_graficos(indicadores_selecionados, anos_selecionados):
    ativo = 'ASAI3.SA'
    graficos = []
    diferenca_legenda = ''

    for indicador in indicadores_selecionados:
        traces = []

        # Criar um gráfico separado para cada indicador
        for ano in anos_selecionados:
            valor = dados[ativo][indicador].get(ano, {}).get('valor', None)
            ano_formatado = datetime.strptime(ano, '%Y-%m-%d').year
            if valor is not None:
                traces.append(go.Bar(
                    x=[ano_formatado],
                    y=[valor],
                    name=f"({ano})"
                ))

        # Calcular a diferença entre os anos
        if len(anos_selecionados) == 2:
            ano_maior = max(anos_selecionados)
            ano_menor = min(anos_selecionados)
            valor_maior = dados[ativo][indicador].get(ano_maior, {}).get('valor', None)
            valor_menor = dados[ativo][indicador].get(ano_menor, {}).get('valor', None)

            if valor_maior is not None and valor_menor is not None:
                diferenca = valor_maior - valor_menor
                diferenca_legenda += f'Diferença para {indicador}: {ano_maior} - {ano_menor} = {diferenca:.2f}'

        # Layout para o gráfico de cada indicador
        layout = go.Layout(
            title=f'{indicador}',
            barmode='group',
            xaxis={'title': 'Ano'},
            yaxis={'title': 'Valor'}
        )

        # Adicionar o gráfico ao layout
        grafico = dcc.Graph(
            figure={'data': traces, 'layout': layout},
            id=f'graph-{indicador}'
        )

        # Adicionar o gráfico à lista de gráficos
        graficos.append(dbc.Col(grafico, width=4))  # Cada gráfico ocupa 4 colunas (1/3 da largura)

    # Organizar os gráficos em uma grade
    graficos_layout = [dbc.Row(graficos[i:i+3], className='mb-4') for i in range(0, len(graficos), 3)]  # 3 gráficos por linha

    return graficos_layout, diferenca_legenda

# Executar o app
if __name__ == '__main__':
    app.run_server(debug=True)

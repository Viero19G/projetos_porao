# Análise e Previsão de Ações com Geração de Relatório PDF
# Autor: Assistente IA
# Data: 2025

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import pdfkit
from jinja2 import Template
import warnings
from datetime import datetime, timedelta
import os
import base64
from io import BytesIO
import time
import random
import pickle

warnings.filterwarnings('ignore')

class StockAnalyzer:
    def __init__(self, ticker_symbol):
        self.ticker = ticker_symbol
        self.data = None
        self.model = None
        self.scaler = StandardScaler()
        self.predictions = {}
        
    def fetch_data(self, period="2y", use_cache=True):
        """Busca dados históricos do ativo com cache e retry usando melhores práticas"""
        cache_file = f"{self.ticker}_cache.pkl"
        
        # Tentar carregar do cache se existir e for recente (menos de 4 horas)
        if use_cache and os.path.exists(cache_file):
            try:
                cache_time = os.path.getmtime(cache_file)
                if time.time() - cache_time < 14400:  # 4 horas
                    with open(cache_file, 'rb') as f:
                        self.data = pickle.load(f)
                    print(f"✅ Dados carregados do cache para {self.ticker}: {len(self.data)} registros")
                    return True
            except Exception as e:
                print(f"⚠️ Erro ao carregar cache: {e}")
        
        # Habilitar modo debug do yfinance para melhor diagnóstico
        yf.enable_debug_mode()
        
        # Configurações globais do yfinance
        print("🔧 Configurando yfinance...")
        
        # Buscar dados online com múltiplas estratégias
        strategies = [
            ("download_function", self._fetch_with_download, period),
            ("ticker_class", self._fetch_with_ticker, period),
            ("ticker_simple", self._fetch_with_simple_ticker, period)
        ]
        
        for strategy_name, method, param in strategies:
            try:
                print(f"🎯 Estratégia: {strategy_name}")
                result = method(param)
                
                if result and len(result) > 0:
                    self.data = result
                    
                    # Salvar no cache
                    with open(cache_file, 'wb') as f:
                        pickle.dump(self.data, f)
                    
                    print(f"✅ Dados obtidos para {self.ticker}: {len(self.data)} registros")
                    return True
                    
            except Exception as e:
                print(f"❌ Falha na estratégia {strategy_name}: {e}")
                continue
        
        print("🔄 Todas as estratégias falharam. Usando dados de exemplo...")
        return self.create_sample_data()
    
    def _fetch_with_download(self, period):
        """Estratégia 1: Usar yf.download() com configurações otimizadas"""
        print("   📡 Usando yf.download()...")
        
        # Calcular datas baseadas no período
        end_date = datetime.now()
        if period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "2y":
            start_date = end_date - timedelta(days=730)
        else:
            start_date = end_date - timedelta(days=365)
        
        # Delay inicial
        time.sleep(random.uniform(1, 3))
        
        data = yf.download(
            self.ticker, 
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            progress=False,
            show_errors=False,
            threads=False  # Reduzir concorrência
        )
        
        # Verificar se dados foram retornados
        if data.empty:
            raise Exception("DataFrame vazio retornado")
            
        # Se multi-level columns, simplificar
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
            
        return data
    
    def _fetch_with_ticker(self, period):
        """Estratégia 2: Usar Ticker.history() com parâmetros otimizados"""
        print("   🎪 Usando Ticker.history()...")
        
        time.sleep(random.uniform(2, 4))
        
        ticker = yf.Ticker(self.ticker)
        
        # Tentar diferentes parâmetros
        params_list = [
            {"period": period, "interval": "1d", "auto_adjust": True, "prepost": True},
            {"period": period, "interval": "1d", "auto_adjust": True, "prepost": False},
            {"period": period, "interval": "1d", "auto_adjust": False, "prepost": False},
        ]
        
        for params in params_list:
            try:
                data = ticker.history(**params)
                if not data.empty:
                    return data
            except:
                continue
                
        raise Exception("Todas as variações de parâmetros falharam")
    
    def _fetch_with_simple_ticker(self, period):
        """Estratégia 3: Ticker simples com mínimos parâmetros"""
        print("   🎯 Usando Ticker simples...")
        
        time.sleep(random.uniform(3, 6))
        
        ticker = yf.Ticker(self.ticker)
        
        # Método mais simples possível
        data = ticker.history(period=period)
        
        if data.empty:
            raise Exception("DataFrame vazio")
            
        return data
    
    def create_sample_data(self):
        """Cria dados de exemplo para demonstração"""
        print("Criando dados de exemplo para demonstração...")
        
        # Gerar dados sintéticos baseados em movimento browniano
        np.random.seed(42)
        n_days = 500
        dates = pd.date_range(start='2022-01-01', periods=n_days, freq='D')
        
        # Preço inicial
        initial_price = 100
        returns = np.random.normal(0.001, 0.02, n_days)  # Retornos diários
        prices = [initial_price]
        
        for i in range(1, n_days):
            prices.append(prices[-1] * (1 + returns[i]))
        
        # Volume sintético
        volumes = np.random.normal(1000000, 200000, n_days)
        volumes = np.abs(volumes).astype(int)
        
        # Criar DataFrame
        self.data = pd.DataFrame({
            'Open': prices,
            'High': [p * random.uniform(1.001, 1.02) for p in prices],
            'Low': [p * random.uniform(0.98, 0.999) for p in prices],
            'Close': prices,
            'Volume': volumes
        }, index=dates)
        
        print(f"Dados de exemplo criados para {self.ticker}: {len(self.data)} registros")
        return True
    
    def prepare_features(self, lookback_days=20):
        """Prepara features para o modelo de regressão"""
        if self.data is None:
            return None
            
        df = self.data.copy()
        
        # Criar features técnicas
        df['MA_5'] = df['Close'].rolling(window=5).mean()
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        df['RSI'] = self.calculate_rsi(df['Close'])
        df['Volatility'] = df['Close'].rolling(window=20).std()
        df['Price_Change'] = df['Close'].pct_change()
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        
        # Criar features de lag (valores anteriores)
        for i in range(1, lookback_days + 1):
            df[f'Close_lag_{i}'] = df['Close'].shift(i)
            df[f'Volume_lag_{i}'] = df['Volume'].shift(i)
        
        # Remover NaN
        df = df.dropna()
        
        # Separar features e target
        feature_cols = [col for col in df.columns if 'lag_' in col or col in ['MA_5', 'MA_20', 'RSI', 'Volatility', 'Volume_MA']]
        X = df[feature_cols]
        y = df['Close']
        
        return X, y, df
    
    def calculate_rsi(self, prices, period=14):
        """Calcula o RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def train_model(self):
        """Treina o modelo de regressão linear"""
        X, y, processed_data = self.prepare_features()
        
        if X is None:
            return False
            
        # Dividir dados em treino e teste
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Escalar features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Treinar modelo
        self.model = LinearRegression()
        self.model.fit(X_train_scaled, y_train)
        
        # Avaliar modelo
        y_pred = self.model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"Modelo treinado - MSE: {mse:.4f}, R²: {r2:.4f}")
        
        self.processed_data = processed_data
        return True
    
    def predict_next_values(self, days=5):
        """Prediz os próximos valores com cenários otimista e pessimista"""
        if self.model is None:
            return None
            
        # Usar os últimos dados para predição
        last_data = self.processed_data.tail(1)
        feature_cols = [col for col in self.processed_data.columns if 'lag_' in col or col in ['MA_5', 'MA_20', 'RSI', 'Volatility', 'Volume_MA']]
        
        predictions = []
        last_features = last_data[feature_cols].values
        
        # Calcular volatilidade histórica para cenários
        historical_volatility = self.data['Close'].pct_change().std()
        
        for day in range(days):
            # Predição base
            last_features_scaled = self.scaler.transform(last_features)
            base_pred = self.model.predict(last_features_scaled)[0]
            
            # Cenários com base na volatilidade
            optimistic = base_pred * (1 + historical_volatility * 2)  # Cenário otimista
            pessimistic = base_pred * (1 - historical_volatility * 2)  # Cenário pessimista
            
            predictions.append({
                'day': day + 1,
                'base': base_pred,
                'optimistic': optimistic,
                'pessimistic': pessimistic
            })
            
            # Atualizar features para próxima predição (simplificado)
            last_features = np.roll(last_features, -1)
            last_features[0, -1] = base_pred
        
        self.predictions = predictions
        return predictions
    
    def create_chart(self):
        """Cria gráfico com dados históricos e previsões"""
        plt.style.use('seaborn-v0_8')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Gráfico 1: Dados históricos e previsões
        dates = self.data.index
        closes = self.data['Close']
        
        # Dados históricos
        ax1.plot(dates, closes, label='Preço Histórico', color='blue', linewidth=2)
        ax1.plot(dates, self.data['Close'].rolling(20).mean(), 
                label='Média Móvel 20', color='orange', alpha=0.7)
        
        # Previsões
        if self.predictions:
            last_date = dates[-1]
            pred_dates = [last_date + timedelta(days=i) for i in range(1, 6)]
            
            base_values = [p['base'] for p in self.predictions]
            optimistic_values = [p['optimistic'] for p in self.predictions]
            pessimistic_values = [p['pessimistic'] for p in self.predictions]
            
            ax1.plot(pred_dates, base_values, 'o-', color='yellow', 
                    linewidth=3, markersize=8, label='Previsão Base')
            ax1.plot(pred_dates, optimistic_values, 's-', color='gold', 
                    linewidth=2, markersize=6, label='Cenário Otimista')
            ax1.plot(pred_dates, pessimistic_values, '^-', color='orange', 
                    linewidth=2, markersize=6, label='Cenário Pessimista')
            
            # Área entre cenários
            ax1.fill_between(pred_dates, pessimistic_values, optimistic_values, 
                           color='yellow', alpha=0.3, label='Faixa de Previsão')
        
        ax1.set_title(f'Análise de Preços - {self.ticker}', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Data')
        ax1.set_ylabel('Preço (USD)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Gráfico 2: Volume
        ax2.bar(dates, self.data['Volume'], alpha=0.6, color='gray')
        ax2.set_title('Volume de Negociação', fontsize=14)
        ax2.set_xlabel('Data')
        ax2.set_ylabel('Volume')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Salvar gráfico
        chart_path = f'{self.ticker}_analysis.png'
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        return chart_path
    
    def generate_report_html(self, chart_path):
        """Gera relatório HTML usando Jinja2"""
        
        # Converter imagem para base64
        with open(chart_path, 'rb') as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()
        
        # Template HTML
        template_str = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Relatório de Análise - {{ ticker }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; color: #2c3e50; }
                .section { margin: 20px 0; }
                .prediction-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                .prediction-table th, .prediction-table td { 
                    border: 1px solid #ddd; padding: 8px; text-align: center; 
                }
                .prediction-table th { background-color: #f2f2f2; }
                .stats { display: flex; justify-content: space-around; }
                .stat-box { text-align: center; padding: 10px; background: #f8f9fa; border-radius: 5px; }
                .chart { text-align: center; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Relatório de Análise Financeira</h1>
                <h2>{{ ticker }}</h2>
                <p>Data: {{ current_date }}</p>
            </div>
            
            <div class="section">
                <h3>Estatísticas Atuais</h3>
                <div class="stats">
                    <div class="stat-box">
                        <h4>Preço Atual</h4>
                        <p>${{ current_price }}</p>
                    </div>
                    <div class="stat-box">
                        <h4>Variação (30d)</h4>
                        <p>{{ price_change_30d }}%</p>
                    </div>
                    <div class="stat-box">
                        <h4>Volume Médio</h4>
                        <p>{{ avg_volume }}</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h3>Previsões para os Próximos 5 Dias</h3>
                <table class="prediction-table">
                    <tr>
                        <th>Dia</th>
                        <th>Previsão Base</th>
                        <th>Cenário Otimista</th>
                        <th>Cenário Pessimista</th>
                    </tr>
                    {% for pred in predictions %}
                    <tr>
                        <td>{{ pred.day }}</td>
                        <td>${{ "%.2f"|format(pred.base) }}</td>
                        <td>${{ "%.2f"|format(pred.optimistic) }}</td>
                        <td>${{ "%.2f"|format(pred.pessimistic) }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
            
            <div class="chart">
                <h3>Gráfico de Análise</h3>
                <img src="data:image/png;base64,{{ chart_base64 }}" style="max-width: 100%; height: auto;">
            </div>
            
            <div class="section">
                <h3>Metodologia</h3>
                <p>Este relatório utiliza regressão linear com features técnicas para prever preços futuros. 
                Os cenários otimista e pessimista são calculados com base na volatilidade histórica do ativo.</p>
                <p><strong>Aviso:</strong> Este relatório é apenas para fins educacionais e não constitui recomendação de investimento.</p>
            </div>
        </body>
        </html>
        '''
        
        template = Template(template_str)
        
        # Calcular estatísticas
        current_price = self.data['Close'].iloc[-1]
        price_30d_ago = self.data['Close'].iloc[-30] if len(self.data) >= 30 else self.data['Close'].iloc[0]
        price_change_30d = ((current_price - price_30d_ago) / price_30d_ago) * 100
        avg_volume = self.data['Volume'].mean()
        
        html_content = template.render(
            ticker=self.ticker,
            current_date=datetime.now().strftime('%d/%m/%Y'),
            current_price=f"{current_price:.2f}",
            price_change_30d=f"{price_change_30d:.2f}",
            avg_volume=f"{avg_volume:,.0f}",
            predictions=self.predictions,
            chart_base64=img_base64
        )
        
        return html_content
    
    def generate_pdf_report(self, chart_path):
        """Gera relatório em PDF"""
        html_content = self.generate_report_html(chart_path)
        
        # Salvar HTML temporário
        html_file = f'{self.ticker}_report.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        try:
            # Configurações do PDF
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            # Gerar PDF
            pdf_file = f'{self.ticker}_report.pdf'
            pdfkit.from_file(html_file, pdf_file, options=options)
            
            print(f"Relatório PDF gerado: {pdf_file}")
            
            # Limpar arquivo HTML temporário
            os.remove(html_file)
            
            return pdf_file
            
        except Exception as e:
            print(f"Erro ao gerar PDF: {e}")
            print("Verifique se o wkhtmltopdf está instalado no sistema")
            return html_file
    
    def run_complete_analysis(self, use_cache=True):
        """Executa análise completa"""
        print("="*60)
        print("🚀 INICIANDO ANÁLISE COMPLETA DE AÇÕES")
        print("="*60)
        
        # 1. Buscar dados
        print("\n📊 Etapa 1: Buscando dados históricos...")
        if not self.fetch_data(use_cache=use_cache):
            print("❌ Falha ao obter dados. Tentando com período menor...")
            if not self.fetch_data(period="1y", use_cache=use_cache):
                print("❌ Não foi possível obter dados.")
                return False
        
        # 2. Treinar modelo
        print("\n🤖 Etapa 2: Treinando modelo de Machine Learning...")
        if not self.train_model():
            print("❌ Falha no treinamento do modelo.")
            return False
        
        # 3. Fazer previsões
        print("\n🔮 Etapa 3: Gerando previsões...")
        predictions = self.predict_next_values()
        if not predictions:
            print("❌ Falha nas previsões.")
            return False
        
        # 4. Criar gráfico
        print("\n📈 Etapa 4: Criando visualizações...")
        chart_path = self.create_chart()
        
        # 5. Gerar relatório PDF
        print("\n📄 Etapa 5: Gerando relatório PDF...")
        try:
            report_path = self.generate_pdf_report(chart_path)
        except Exception as e:
            print(f"⚠️ Erro ao gerar PDF: {e}")
            print("💡 Gerando apenas relatório HTML...")
            report_path = self.generate_html_report(chart_path)
        
        print("\n" + "="*60)
        print("✅ ANÁLISE COMPLETA FINALIZADA!")
        print("="*60)
        print(f"📁 Arquivos gerados:")
        print(f"   📈 Gráfico: {chart_path}")
        print(f"   📄 Relatório: {report_path}")
        print("="*60)
        
        return True
    
    def generate_html_report(self, chart_path):
        """Gera apenas relatório HTML (fallback se PDF falhar)"""
        html_content = self.generate_report_html(chart_path)
        html_file = f'{self.ticker}_report.html'
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Relatório HTML gerado: {html_file}")
        return html_file

# Exemplo de uso
if __name__ == "__main__":
    print("🎯 ANALISADOR DE AÇÕES COM IA")
    print("="*50)
    
    # Lista de tickers populares para teste
    popular_tickers = {
        "1": ("AAPL", "Apple Inc."),
        "2": ("MSFT", "Microsoft Corp."),
        "3": ("GOOGL", "Alphabet Inc."),
        "4": ("TSLA", "Tesla Inc."),
        "5": ("PETR4.SA", "Petrobras (Brasil)"),
        "6": ("VALE3.SA", "Vale (Brasil)"),
        "7": ("CUSTOM", "Inserir ticker personalizado")
    }
    
    print("\nEscolha uma opção:")
    for key, (ticker, name) in popular_tickers.items():
        if key != "7":
            print(f"{key}. {ticker} - {name}")
        else:
            print(f"{key}. {name}")
    
    try:
        choice = input("\nDigite sua escolha (1-7): ").strip()
        
        if choice == "7":
            ticker_symbol = input("Digite o ticker desejado (ex: AAPL, PETR4.SA): ").strip().upper()
        elif choice in popular_tickers:
            ticker_symbol = popular_tickers[choice][0]
        else:
            print("Opção inválida. Usando AAPL como padrão.")
            ticker_symbol = "AAPL"
        
        print(f"\n🎯 Analisando: {ticker_symbol}")
        
        # Perguntar sobre cache
        use_cache_input = input("Usar cache de dados (recomendado para evitar rate limiting)? (s/n): ").strip().lower()
        use_cache = use_cache_input != 'n'
        
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
        exit()
    except:
        print("Usando configurações padrão: AAPL com cache habilitado")
        ticker_symbol = "AAPL"
        use_cache = True
    
    # Criar analisador
    analyzer = StockAnalyzer(ticker_symbol)
    
    # Executar análise completa
    success = analyzer.run_complete_analysis(use_cache=use_cache)
    
    if success:
        print("\n" + "🔮 PREVISÕES PARA OS PRÓXIMOS 5 DIAS:")
        print("="*60)
        for pred in analyzer.predictions:
            print(f"📅 Dia {pred['day']:2d}: "
                  f"Base ${pred['base']:8.2f} | "
                  f"📈 Otimista ${pred['optimistic']:8.2f} | "
                  f"📉 Pessimista ${pred['pessimistic']:8.2f}")
        
        print("\n💡 Dicas:")
        print("• Previsões são baseadas em análise técnica e modelo de ML")
        print("• Use apenas como referência, não como conselho de investimento")
        print("• Considere sempre outros fatores fundamentais")
        
    else:
        print("\n❌ Falha na análise.")
        print("💡 Possíveis soluções:")
        print("• Verifique sua conexão com a internet")
        print("• Tente novamente em alguns minutos")
        print("• Use um ticker diferente")
        print("• Execute com dados de exemplo (modo offline)")
        
        # Oferecer modo de exemplo
        try_example = input("\nDeseja tentar com dados de exemplo? (s/n): ").strip().lower()
        if try_example == 's':
            analyzer.ticker = "EXEMPLO_" + ticker_symbol
            if analyzer.create_sample_data():
                analyzer.run_complete_analysis(use_cache=False)
import psycopg2

# Configurações do banco de dados
db_config = {
    "dbname": "ativos_db",
    "user": "gabriel",
    "password": "Su1tdr34ms*22",
    "host": "localhost",
    "port": 5432
}

# Conexão com o banco de dados
try:
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Exemplo: Inserir dados na tabela ATIVO
    cursor.execute("""
        INSERT INTO ATIVO (TICKER, TIPO, DIVIDENDOS) VALUES 
        ('PETR4', 'AÇÃO', TRUE),
        ('VALE3', 'AÇÃO', FALSE)
        ON CONFLICT (TICKER) DO NOTHING;
    """)

    # Exemplo: Inserir dados na tabela ANALISE
    cursor.execute("""
        INSERT INTO ANALISE (SINAL, PRECO, TICKER) VALUES 
        ('COMPRA', 26.75, 'PETR4'),
        ('VENDA', 89.15, 'VALE3');
    """)

    conn.commit()
    print("Dados inseridos com sucesso!")

except Exception as e:
    print("Erro ao conectar ao banco:", e)

finally:
    if conn:
        cursor.close()
        conn.close()

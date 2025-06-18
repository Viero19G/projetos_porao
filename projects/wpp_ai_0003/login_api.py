
import requests
import json
import sys
from typing import Optional, Dict, Any

# Configurações da API
BASE_URL = "http://localhost:8000/"  # Altere para o URL da sua API
LOGIN_ENDPOINT = "api/token/"

def fazer_login(username: str, password: str, base_url: str = BASE_URL) -> Optional[Dict[str, Any]]:
    """
    Faz login na API e retorna os dados da resposta
    
    Args:
        username: Nome de usuário
        password: Senha
        base_url: URL base da API
        
    Returns:
        Dict com os dados da resposta ou None se houver erro
    """
    url = f"{base_url}{LOGIN_ENDPOINT}"
    
    # Dados para enviar no POST
    dados_login = {
        "username": username,
        "password": password
    }
    
    # Headers da requisição
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print(f"Fazendo login em: {url}")
        print(f"Usuário: {username}")
        
        # Fazer a requisição POST
        response = requests.post(
            url=url,
            json=dados_login,
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            dados = response.json()
            print("✅ Login realizado com sucesso!")
            return dados
            
        else:
            print("❌ Erro no login:")
            try:
                erro = response.json()
                print(f"Erro: {erro}")
            except:
                print(f"Erro HTTP: {response.status_code}")
                print(f"Texto da resposta: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        return None

def salvar_token(dados_resposta: Dict[str, Any], arquivo: str = "token.txt") -> None:
    """
    Salva o access token em um arquivo
    """
    try:
        access_token = dados_resposta.get('access')
        if access_token:
            with open(arquivo, 'w') as f:
                f.write(access_token)
            print(f"✅ Token salvo em: {arquivo}")
        else:
            print("❌ Access token não encontrado na resposta")
    except Exception as e:
        print(f"❌ Erro ao salvar token: {e}")

def testar_token(token: str, base_url: str = BASE_URL) -> None:
    """
    Testa se o token está funcionando fazendo uma requisição para /api/profile/
    """
    url = f"{base_url}/api/profile/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"\nTestando token em: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            print("✅ Token válido!")
            print(f"Usuário logado: {dados.get('username')}")
        else:
            print("❌ Token inválido ou expirado")
            print(f"Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao testar token: {e}")

def main():
    """
    Função principal do script
    """
    print("=== Script de Login API Django ===\n")
    
    # Solicitar credenciais do usuário
    if len(sys.argv) >= 3:
        # Usar argumentos da linha de comando
        username = sys.argv[1]
        password = sys.argv[2]
        base_url = sys.argv[3] if len(sys.argv) > 3 else BASE_URL
    else:
        # Solicitar input do usuário
        username = input("Digite o username: ").strip()
        password = input("Digite a password: ").strip()
        
        url_input = input(f"Digite a URL da API (Enter para usar {BASE_URL}): ").strip()
        base_url = url_input if url_input else BASE_URL
    
    if not username or not password:
        print("❌ Username e password são obrigatórios!")
        sys.exit(1)
    
    # Fazer login
    dados_resposta = fazer_login(username, password, base_url)
    
    if dados_resposta:
        print("\n=== Dados da Resposta ===")
        print(json.dumps(dados_resposta, indent=2, ensure_ascii=False))
        
        # Salvar token
        salvar_token(dados_resposta)
        
        # Testar token
        access_token = dados_resposta.get('access_token')
        if access_token:
            testar_token(access_token, base_url)
        
        print(f"\n✅ Access Token: {dados_resposta.get('access_token')}")
        print(f"✅ Refresh Token: {dados_resposta.get('refresh_token')}")
        
    else:
        print("❌ Não foi possível fazer login")
        sys.exit(1)

if __name__ == "__main__":
    main()
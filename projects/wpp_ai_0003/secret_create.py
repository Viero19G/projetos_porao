#!/usr/bin/env python3
"""
Script para gerar uma SECRET_KEY segura para Django
"""

from django.core.management.utils import get_random_secret_key

def generate_secret_key():
    """Gera uma nova SECRET_KEY"""
    key = get_random_secret_key()
    print("Nova SECRET_KEY gerada:")
    print(f"SECRET_KEY={key}")
    print("\nAdicione esta linha ao seu arquivo .env")
    return key

if __name__ == "__main__":
    generate_secret_key()
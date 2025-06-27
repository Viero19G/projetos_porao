// src/hooks/useAuth.ts
// ESTA É A VERSÃO FUNCIONAL E COMPLETA DO HOOK DE AUTENTICAÇÃO.
// Ela lida com a lógica de login, registro, logout e gerenciamento de tokens.

'use client';

import { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { login, logout, register } from '@/lib/api';
import React from 'react';

// Interface para o objeto de usuário armazenado no contexto
interface User {
    isAuthenticated: boolean;
    username: string;
    id?: number; // Opcional, caso o ID do usuário venha da API
}

// Tipo de retorno para as funções handleLogin e handleRegister
// Define 'error' explicitamente como string | undefined para garantir consistência
type AuthResult = { success: boolean; error: string | undefined };

// Interface para o valor fornecido pelo AuthContext
interface AuthContextValue {
    user: User | null;
    loading: boolean;
    handleLogin: (username: string, password: string) => Promise<AuthResult>;
    handleRegister: (username: string, email: string, password: string) => Promise<AuthResult>;
    handleLogout: () => void;
}

// Criação do Contexto de Autenticação.
// EXPORTADO para ser acessível aos componentes que precisam do Provider.
export const AuthContext = createContext<AuthContextValue | null>(null);

// Componente Provedor de Autenticação
// Ele encapsula a lógica de autenticação e fornece o estado e as funções para seus filhos.
export const AuthProvider = ({ children }: { children: ReactNode }): JSX.Element => {
    // Estados para gerenciar as informações do usuário e o status de carregamento
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    // Hook do Next.js para manipulação de rotas
    const router = useRouter();

    // Efeito para carregar o estado do usuário ao iniciar a aplicação (ex: verificar token no localStorage)
    useEffect(() => {
        const loadUser = async () => {
            if (typeof window !== 'undefined') {
                const token = localStorage.getItem('access_token');
                if (token) {
                    // Em um cenário real, o ideal é decodificar o token JWT aqui
                    // ou fazer uma chamada para um endpoint '/me' na sua API
                    // para obter os dados reais do usuário (username, id, etc.).
                    // Por simplicidade, estamos definindo um usuário genérico.
                    setUser({ isAuthenticated: true, username: 'Usuário Logado', id: 1 });
                }
            }
            // Marca o carregamento como concluído
            setLoading(false);
        };
        loadUser();
    }, []); // O array vazio garante que este efeito seja executado apenas uma vez, ao montar o componente

    // Função assíncrona para lidar com o login do usuário
    const handleLogin = async (username: string, password: string): Promise<AuthResult> => {
        setLoading(true); // Ativa o estado de carregamento
        try {
            // Chama a função de login da sua API (de '@/lib/api')
            await login(username, password);
            // Define o usuário como autenticado (com dados que viriam da resposta da API)
            setUser({ isAuthenticated: true, username: username, id: 1 });
            // Redireciona para o dashboard após o login bem-sucedido
            router.push('/dashboard');
            // Retorna sucesso e 'error' como undefined, conforme o tipo AuthResult
            return { success: true, error: undefined };
        } catch (error: any) {
            console.error('Erro no login:', error);
            setUser(null); // Limpa o usuário em caso de erro de login
            // Extrai a mensagem de erro da resposta da API ou usa uma mensagem genérica
            const errorMessage = error.response?.data?.detail || error.response?.data?.non_field_errors?.[0] || 'Erro ao fazer login';
            // Retorna falha e a mensagem de erro
            return { success: false, error: errorMessage };
        } finally {
            setLoading(false); // Desativa o estado de carregamento
        }
    };

    // Função assíncrona para lidar com o registro de um novo usuário
    const handleRegister = async (username: string, email: string, password: string): Promise<AuthResult> => {
        setLoading(true); // Ativa o estado de carregamento
        try {
            // Chama a função de registro da sua API (de '@/lib/api')
            await register(username, email, password);
            // Após o registro, tenta logar o usuário automaticamente
            await login(username, password);
            // Define o usuário como autenticado
            setUser({ isAuthenticated: true, username: username, id: 1 });
            // Redireciona para o dashboard
            router.push('/dashboard');
            // Retorna sucesso e 'error' como undefined
            return { success: true, error: undefined };
        } catch (error: any) {
            console.error('Erro no registro:', error);
            // Extrai a mensagem de erro específica da resposta da API para registro
            const errorMessage = error.response?.data?.username?.[0] ||
                                 error.response?.data?.email?.[0] ||
                                 error.response?.data?.password?.[0] ||
                                 error.response?.data?.detail ||
                                 'Erro ao registrar';
            // Retorna falha e a mensagem de erro
            return { success: false, error: errorMessage };
        } finally {
            setLoading(false); // Desativa o estado de carregamento
        }
    };

    // Função para lidar com o logout do usuário
    const handleLogout = () => {
        logout(); // Chama a função de logout (que remove os tokens do localStorage)
        setUser(null); // Limpa o estado do usuário
        router.push('/auth'); // Redireciona para a página de autenticação
    };

    // Renderiza o provedor de contexto, passando o estado do usuário, loading e as funções de manipulação
    return (
        <AuthContext.Provider value={{ user, loading, handleLogin, handleRegister, handleLogout }}>
            {children}
        </AuthContext.Provider>
    );
};

// Hook personalizado para consumir o contexto de autenticação
// Ele fornece acesso ao estado e às funções definidas no AuthProvider
export const useAuth = () => {
    const context = useContext(AuthContext);
    // Garante que o hook seja usado apenas dentro de um AuthProvider
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

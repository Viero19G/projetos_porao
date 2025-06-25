// src/hooks/useAuth.ts
'use client';

import { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { login, logout, register } from '@/lib/api';
import React from 'react'; // Certifique-se de que React está importado

interface User {
    isAuthenticated: boolean;
    username: string;
    id?: number;
}

interface AuthContextValue {
    user: User | null;
    loading: boolean;
    handleLogin: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
    handleRegister: (username: string, email: string, password: string) => Promise<{ success: boolean; error?: string }>;
    handleLogout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// **CORREÇÃO FINAL PARA AUTHPROVIDER:** Tipar explicitamente o retorno da função como JSX.Element
// Isso força o TypeScript a reconhecer o que o componente está retornando.
export const AuthProvider = ({ children }: { children: ReactNode }): JSX.Element => { // <--- MUDANÇA AQUI
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        const loadUser = async () => {
            if (typeof window !== 'undefined') {
                const token = localStorage.getItem('access_token');
                if (token) {
                    setUser({ isAuthenticated: true, username: 'Usuário Logado', id: 1 });
                }
            }
            setLoading(false);
        };
        loadUser();
    }, []);

    const handleLogin = async (username: string, password: string) => {
        setLoading(true);
        try {
            await login(username, password);
            setUser({ isAuthenticated: true, username: username, id: 1 });
            router.push('/dashboard');
            return { success: true };
        } catch (error: any) {
            console.error('Erro no login:', error);
            setUser(null);
            return { success: false, error: error.response?.data?.detail || 'Erro ao fazer login' };
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (username: string, email: string, password: string) => {
        setLoading(true);
        try {
            await register(username, email, password);
            await login(username, password);
            setUser({ isAuthenticated: true, username: username, id: 1 });
            router.push('/dashboard');
            return { success: true };
        } catch (error: any) {
            console.error('Erro no registro:', error);
            return { success: false, error: error.response?.data?.username?.[0] || error.response?.data?.email?.[0] || error.response?.data?.password?.[0] || 'Erro ao registrar' };
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        logout();
        setUser(null);
        router.push('/auth');
    };

    return (
        <AuthContext.Provider value={{ user, loading, handleLogin, handleRegister, handleLogout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
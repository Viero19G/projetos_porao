// src/app/auth/page.tsx
'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { AuthForm } from '@/components/AuthForm'; // Certifique-se de que o caminho está correto
import { useAuth } from '@/hooks/useAuth'; // Importe o hook de autenticação

export default function AuthPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    // Determina se é para mostrar o formulário de 'login' ou 'register' com base na URL
    const type = searchParams.get('type') === 'register' ? 'register' : 'login';

    const { user, loading } = useAuth(); // Use o hook de autenticação para verificar o estado

    useEffect(() => {
        // Se o carregamento terminou e o usuário está autenticado, redireciona para o dashboard
        if (!loading && user?.isAuthenticated) {
            router.push('/dashboard');
        }
        // Se o carregamento terminou e o usuário NÃO está autenticado,
        // permanece na página de autenticação para exibir o formulário.
    }, [user, loading, router]); // Dependências para re-executar o efeito quando user ou loading mudarem

    // Enquanto estiver carregando ou se o usuário já estiver autenticado (e o redirecionamento ainda não ocorreu)
    if (loading || user?.isAuthenticated) {
        return (
            <div className="flex justify-center items-center min-h-[calc(100vh-64px)]">
                <p>Carregando...</p>
            </div>
        );
    }

    // Se o usuário não está autenticado e o carregamento terminou, exibe o formulário de autenticação
    return (
        <div className="flex justify-center items-center min-h-[calc(100vh-64px)]">
            <AuthForm type={type} />
        </div>
    );
}
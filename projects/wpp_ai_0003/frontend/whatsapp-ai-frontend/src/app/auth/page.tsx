// src/app/auth/page.tsx
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function AuthPage() {
    const router = useRouter();

    // Redireciona imediatamente, já que não há mais autenticação
    useEffect(() => {
        router.push('/dashboard');
    }, [router]);

    return (
        <div className="flex justify-center items-center min-h-[calc(100vh-64px)]">
            Redirecionando...
        </div>
    );
}
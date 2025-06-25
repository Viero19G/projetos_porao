// src/app/page.tsx
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { Loader2 } from 'lucide-react';

export default function HomePage() {
    const { user, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!loading) {
            if (user?.isAuthenticated) {
                router.push('/dashboard');
            } else {
                router.push('/auth');
            }
        }
    }, [user, loading, router]);

    if (loading) {
        return (
            <div className="flex justify-center items-center min-h-[calc(100vh-64px)]">
                <Loader2 className="mr-2 h-8 w-8 animate-spin" /> Carregando...
            </div>
        );
    }

    return null;
}
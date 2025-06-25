// src/app/dashboard/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { PlusCircle } from 'lucide-react';
import { QRCodeDialog } from '@/components/QRCodeDialog';
import { DeviceList } from '@/components/DeviceList';
import { Loader2 } from 'lucide-react';

export default function DashboardPage() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [refreshConnectionsFlag, setRefreshConnectionsFlag] = useState(false);

    useEffect(() => {
        if (!loading && !user?.isAuthenticated) {
            router.push('/auth');
        }
    }, [user, loading, router]);

    const handleConnectionSuccess = () => {
        setRefreshConnectionsFlag(prev => !prev);
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center min-h-[calc(100vh-64px)]">
                <Loader2 className="mr-2 h-8 w-8 animate-spin" /> Carregando dashboard...
            </div>
        );
    }

    if (!user?.isAuthenticated) {
        return null;
    }

    return (
        <div className="p-4 space-y-8">
            <h1 className="text-3xl font-bold">Olá, {user.username}!</h1>

            <div className="flex justify-end">
                <Button onClick={() => setIsDialogOpen(true)}>
                    <PlusCircle className="mr-2 h-4 w-4" /> Adicionar Novo WhatsApp
                </Button>
            </div>

            <QRCodeDialog
                open={isDialogOpen}
                onOpenChange={setIsDialogOpen}
                // User ID deve ser um número ou string que sua API DRF usa para identificar o usuário.
                // Ajuste esta linha se o `useAuth` retorna um `user.id` diferente ou se `user.id` é string.
                userId={user.id || 1}
                onConnectionSuccess={handleConnectionSuccess}
            />

            <DeviceList userId={user.id || 1} refreshConnections={refreshConnectionsFlag} />
        </div>
    );
}
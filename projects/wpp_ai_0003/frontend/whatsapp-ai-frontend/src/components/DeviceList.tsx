// src/components/DeviceList.tsx
'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Trash2 } from 'lucide-react';
// Se for usar Sonner/Toast:
//import { useToast } from "@/components/ui/use-toast";
import { getUserWhatsappConnections, WhatsappConnection } from '@/lib/api'; // Importe o tipo WhatsappConnection
import { disconnectWhatsappSessionGateway } from '@/lib/gatewayApi';
import { Loader2 } from 'lucide-react';
import { Badge } from "@/components/ui/badge";

interface DeviceListProps {
    userId: number | string;
    refreshConnections: boolean;
}

export function DeviceList({ userId, refreshConnections }: DeviceListProps) {
    const [connections, setConnections] = useState<WhatsappConnection[]>([]);
    const [loading, setLoading] = useState(true);
    const [disconnectingId, setDisconnectingId] = useState<string | null>(null);
    // Se for usar Sonner/Toast:
    //const { toast } = useToast();

    const fetchConnections = useCallback(async () => {
        setLoading(true);
        try {
            const data = await getUserWhatsappConnections();
            setConnections(data);
        } catch (error: any) {
            console.error('Erro ao buscar conexões:', error);
            // Se for usar Sonner/Toast:
            /*toast({
                title: "Erro",
                description: "Não foi possível carregar as conexões.",
                variant: "destructive",
            });*/
        } finally {
            setLoading(false);
        }
    },[]);

    useEffect(() => {
        if (userId) {
            fetchConnections();
        }
    }, [userId, fetchConnections, refreshConnections]);

    const handleDisconnect = async (sessionId: string) => {
        setDisconnectingId(sessionId);
        try {
            await disconnectWhatsappSessionGateway(sessionId);
            // Se for usar Sonner/Toast:
           /* toast({
                title: "Desconectado!",
                description: `A sessão ${sessionId} foi desconectada.`,
            });*/
            fetchConnections();
        } catch (error: any) {
            console.error('Erro ao desconectar:', error);
            // Se for usar Sonner/Toast:
          /*  toast({
                title: "Erro ao desconectar",
                description: error.message || "Ocorreu um erro ao tentar desconectar a sessão.",
                variant: "destructive",
            });*/
        } finally {
            setDisconnectingId(null);
        }
    };

    if (loading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Dispositivos Conectados</CardTitle>
                </CardHeader>
                <CardContent className="flex justify-center items-center h-24">
                    <Loader2 className="mr-2 h-6 w-6 animate-spin" /> Carregando conexões...
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Dispositivos Conectados</CardTitle>
            </CardHeader>
            <CardContent>
                {connections.length === 0 ? (
                    <p className="text-center text-muted-foreground">Nenhuma conexão ativa encontrada.</p>
                ) : (
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Nome da Conexão</TableHead>
                                <TableHead>Número do WhatsApp</TableHead>
                                <TableHead>Agente IA</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead className="text-right">Ações</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {connections.map((conn) => (
                                <TableRow key={conn.session_id}>
                                    <TableCell className="font-medium">{conn.name}</TableCell>
                                    <TableCell>{conn.phone_number || 'N/A'}</TableCell>
                                    <TableCell>{conn.agent_name}</TableCell>
                                    <TableCell>
                                        <Badge variant={conn.is_active ? "default" : "destructive"}>
                                            {conn.is_active ? 'Ativo' : 'Inativo'}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <Button
                                            variant="destructive"
                                            size="icon"
                                            onClick={() => handleDisconnect(conn.session_id)}
                                            disabled={disconnectingId === conn.session_id || !conn.is_active}
                                        >
                                            {disconnectingId === conn.session_id ? (
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                            ) : (
                                                <Trash2 className="h-4 w-4" />
                                            )}
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                )}
            </CardContent>
        </Card>
    );
}
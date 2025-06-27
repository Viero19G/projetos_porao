// src/hooks/useWhatsappGateway.ts
'use client';

import { useState, useEffect, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { v4 as uuidv4 } from 'uuid';
import { disconnectWhatsappSessionGateway } from '@/lib/gatewayApi';

const WHATSAPP_GATEWAY_URL = process.env.NEXT_PUBLIC_WHATSAPP_GATEWAY_URL;

interface SessionStatusMap {
    [sessionId: string]: 'initializing' | 'qr_generated' | 'connected' | 'auth_failure' | 'disconnected' | 'error' | 'already_initialized' | 'unknown';
}

// Definição para as informações da sessão, pode ser mais completa se a DRF retornar mais dados
export interface GatewaySessionInfo {
    sessionId: string;
    status: SessionStatusMap[string];
    qrCode: string | null;
}

export const useWhatsappGateway = (userId: number | string) => { // userId pode ser number ou string dependendo da sua DRF
    const [socket, setSocket] = useState<Socket | null>(null);
    const [qrCode, setQrCode] = useState<string | null>(null);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [sessionStatus, setSessionStatus] = useState<SessionStatusMap>({});
    const [isLoadingQr, setIsLoadingQr] = useState(false);

    useEffect(() => {
        if (!userId) return;

        const newSocket: Socket = io(WHATSAPP_GATEWAY_URL as string, {
            transports: ['websocket'],
            autoConnect: false,
            query: { userId: userId.toString() } // Garante que userId é string para o query param
        });

        newSocket.on('connect', () => {
            console.log('Conectado ao Gateway WhatsApp via Socket.IO');
        });

        newSocket.on('qr-code', (data: { sessionId: string; qr: string }) => {
            console.log('QR Code recebido para sessão:', data.sessionId);
            setQrCode(data.qr);
            setCurrentSessionId(data.sessionId);
            setSessionStatus(prev => ({ ...prev, [data.sessionId]: 'qr_generated' }));
            setIsLoadingQr(false);
        });

        newSocket.on('whatsapp-status', (data: { sessionId: string; status: SessionStatusMap[string]; message: string }) => {
            console.log(`Status da sessão ${data.sessionId}: ${data.status} - ${data.message}`);
            setSessionStatus(prev => ({ ...prev, [data.sessionId]: data.status }));
            if (data.status === 'connected') {
                setQrCode(null); // Limpa o QR code em caso de conexão bem-sucedida
                setCurrentSessionId(null); // Limpa o ID da sessão atual, pois ela está conectada
            } else if (data.status === 'disconnected' || data.status === 'auth_failure' || data.status === 'error') {
                setQrCode(null); // Limpa o QR code em caso de falha/desconexão
                setCurrentSessionId(null); // Limpa o ID da sessão atual em caso de falha/desconexão
            }
        });

        newSocket.on('disconnect', () => {
            console.log('Desconectado do Gateway WhatsApp.');
            // Opcional: Você pode querer redefinir todos os status de sessão ou tratá-los de forma diferente
            // setSessionStatus({}); 
            // setCurrentSessionId(null);
            // setQrCode(null);
        });

        newSocket.on('connect_error', (err: Error) => {
            console.error('Erro de conexão com Socket.IO:', err.message);
            setIsLoadingQr(false); // Para o carregamento em caso de erro de conexão
            setQrCode(null); // Limpa o QR se houver um erro de conexão antes que ele seja gerado
            setCurrentSessionId(null);
            setSessionStatus(prev => {
                if (currentSessionId) {
                    return { ...prev, [currentSessionId]: 'error' };
                }
                return prev;
            });
        });

        setSocket(newSocket);
        newSocket.connect();

        return () => {
            newSocket.disconnect();
        };
    }, [userId, currentSessionId]); // currentSessionId adicionado às dependências para garantir que as atualizações de status sejam refletidas corretamente

    const startNewWhatsappSession = useCallback((connectionName: string, agentName: string, agentPrompt: string) => {
        if (!socket || !userId) {
            console.error('Socket não conectado ou User ID ausente.');
            return;
        }
        setIsLoadingQr(true);
        setQrCode(null); // Limpa qualquer QR code anterior
        setCurrentSessionId(null); // Limpa qualquer ID de sessão anterior
        const newSessionId = uuidv4();
        socket.emit('start-whatsapp-session', {
            sessionId: newSessionId,
            userId: userId,
            connectionName,
            agentName,
            agentPrompt
        });
        setCurrentSessionId(newSessionId);
        setSessionStatus(prev => ({ ...prev, [newSessionId]: 'initializing' })); // Define o status inicial
    }, [socket, userId]);

    const disconnectSession = useCallback(async (sessionId: string) => {
        try {
            await disconnectWhatsappSessionGateway(sessionId);
            console.log(`Sessão ${sessionId} desconectada via Gateway.`);
            // O gateway emitirá 'whatsapp-status' com 'disconnected', o que atualizará o estado
            // No entanto, é uma boa prática atualizar otimisticamente a UI aqui também, se necessário
            setSessionStatus(prev => ({ ...prev, [sessionId]: 'disconnected' }));
            if (currentSessionId === sessionId) {
                setCurrentSessionId(null);
                setQrCode(null);
                setIsLoadingQr(false);
            }
        } catch (error) {
            console.error('Erro ao desconectar sessão:', error);
            // Implementar toast ou feedback visual para o usuário
            setSessionStatus(prev => ({ ...prev, [sessionId]: 'error' })); // Define o status de erro em caso de falha da API
        }
    }, [currentSessionId]);

    return {
        qrCode,
        currentSessionId,
        sessionStatus,
        isLoadingQr,
        startNewWhatsappSession,
        disconnectSession,
        // Expõe os setters para melhor controle no componente consumidor, se necessário,
        // embora geralmente eles sejam controlados dentro do hook
        setQrCode,
        setIsLoadingQr
    };
};
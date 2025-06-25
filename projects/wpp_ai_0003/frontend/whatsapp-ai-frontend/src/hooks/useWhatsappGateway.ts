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
                setQrCode(null);
                setCurrentSessionId(null);
            } else if (data.status === 'disconnected' || data.status === 'auth_failure' || data.status === 'error') {
                setQrCode(null);
                setCurrentSessionId(null);
            }
        });

        newSocket.on('disconnect', () => {
            console.log('Desconectado do Gateway WhatsApp.');
        });

        newSocket.on('connect_error', (err: Error) => {
            console.error('Erro de conexão com Socket.IO:', err.message);
        });

        setSocket(newSocket);
        newSocket.connect();

        return () => {
            newSocket.disconnect();
        };
    }, [userId]);

    const startNewWhatsappSession = useCallback((connectionName: string, agentName: string, agentPrompt: string) => {
        if (!socket || !userId) {
            console.error('Socket não conectado ou User ID ausente.');
            return;
        }
        setIsLoadingQr(true);
        const newSessionId = uuidv4();
        socket.emit('start-whatsapp-session', {
            sessionId: newSessionId,
            userId: userId,
            connectionName,
            agentName,
            agentPrompt
        });
        setCurrentSessionId(newSessionId);
    }, [socket, userId]);

    const disconnectSession = useCallback(async (sessionId: string) => {
        try {
            await disconnectWhatsappSessionGateway(sessionId);
            console.log(`Sessão ${sessionId} desconectada via Gateway.`);
            // A atualização do estado 'sessions' será feita pelo DeviceList ao buscar novamente
        } catch (error) {
            console.error('Erro ao desconectar sessão:', error);
            // Implementar toast ou feedback visual para o usuário
        }
    }, []);

    return {
        qrCode,
        currentSessionId,
        sessionStatus,
        isLoadingQr,
        startNewWhatsappSession,
        disconnectSession,
    };
};
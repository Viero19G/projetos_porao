// src/components/QRCodeDialog.tsx
'use client';

import { useState, useEffect } from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useWhatsappGateway } from '@/hooks/useWhatsappGateway';
// Se for usar Sonner/Toast:
import { Loader2 } from 'lucide-react';
// Importe useToast se estiver usando o Sonner/Toast
//import { useToast } from "@/components/ui/use-toast"; // Remova o comentário se for usar

interface QRCodeDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    userId: number | string;
    onConnectionSuccess: () => void;
}

export function QRCodeDialog({ open, onOpenChange, userId, onConnectionSuccess }: QRCodeDialogProps) {
    // **AJUSTE AQUI:** Desestruture setIsLoadingQr e setQrCode
    const { qrCode, currentSessionId, sessionStatus, isLoadingQr, startNewWhatsappSession, setIsLoadingQr, setQrCode } = useWhatsappGateway(userId);
    
    // Se for usar Sonner/Toast:
  //  const { toast } = useToast(); // Remova o comentário se for usar

    const [connectionName, setConnectionName] = useState('');
    const [agentName, setAgentName] = useState('');
    const [agentPrompt, setAgentPrompt] = useState('Comporte-se como um gaúcho do século 19, use expressões típicas e gírias da época e da região, mas seja prestativo.');

    useEffect(() => {
        if (currentSessionId && sessionStatus[currentSessionId] === 'connected') {
            // Se for usar Sonner/Toast:
    /*        toast({ // Remova o comentário
                title: "Conexão estabelecida!",
                description: `Sua conexão "${connectionName}" está ativa.`,
            });*/
            setConnectionName('');
            setAgentName('');
            setAgentPrompt('Comporte-se como um gaúcho do século 19, use expressões típicas e gírias da época e da região, mas seja prestativo.');
            onConnectionSuccess();
            onOpenChange(false);
        } else if (currentSessionId && (sessionStatus[currentSessionId] === 'auth_failure' || sessionStatus[currentSessionId] === 'disconnected' || sessionStatus[currentSessionId] === 'error')) {
            // Se for usar Sonner/Toast:
            /*toast({ // Remova o comentário
                title: "Erro na conexão!",
                description: `A sessão ${currentSessionId} falhou: ${sessionStatus[currentSessionId]}. Tente novamente.`,
                variant: "destructive",
            });*/
            setIsLoadingQr(false);
            setQrCode(null);
        }
    }, [sessionStatus, currentSessionId, onOpenChange, connectionName, onConnectionSuccess, setIsLoadingQr, setQrCode]); // Adicione toast, setIsLoadingQr e setQrCode nas dependências

    const handleStartConnection = () => {
        if (!connectionName || !agentName || !agentPrompt) {
            // Se for usar Sonner/Toast:
            /*toast({ // Remova o comentário
                title: "Preencha todos os campos!",
                description: "Por favor, defina um nome para a conexão, o agente e o prompt.",
                variant: "destructive",
            });*/
            return;
        }
        startNewWhatsappSession(connectionName, agentName, agentPrompt);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Adicionar Nova Conexão WhatsApp</DialogTitle>
                    <DialogDescription>
                        Preencha os detalhes da nova conexão e escaneie o QR Code.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="connectionName" className="text-right">
                            Nome da Conexão
                        </Label>
                        <Input
                            id="connectionName"
                            value={connectionName}
                            onChange={(e) => setConnectionName(e.target.value)}
                            className="col-span-3"
                            disabled={isLoadingQr || qrCode !== null}
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="agentName" className="text-right">
                            Nome do Agente IA
                        </Label>
                        <Input
                            id="agentName"
                            value={agentName}
                            onChange={(e) => setAgentName(e.target.value)}
                            className="col-span-3"
                            disabled={isLoadingQr || qrCode !== null}
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="agentPrompt" className="text-right">
                            Prompt do Agente
                        </Label>
                        <Textarea
                            id="agentPrompt"
                            value={agentPrompt}
                            onChange={(e) => setAgentPrompt(e.target.value)}
                            className="col-span-3"
                            rows={4}
                            disabled={isLoadingQr || qrCode !== null}
                        />
                    </div>

                    <div className="flex justify-center items-center h-48 border rounded-md bg-gray-100 dark:bg-gray-700">
                        {isLoadingQr && (
                            <div className="flex flex-col items-center">
                                <Loader2 className="mr-2 h-8 w-8 animate-spin" />
                                <p className="mt-2 text-sm text-muted-foreground">Gerando QR Code...</p>
                            </div>
                        )}
                        {qrCode && !isLoadingQr && (
                            <div className="flex flex-col items-center">
                                <p className="mb-2 text-sm text-center">Escaneie com seu WhatsApp:</p>
                                <img src={qrCode} alt="QR Code" className="w-40 h-40 object-contain" />
                                {currentSessionId && sessionStatus[currentSessionId] === 'qr_generated' && (
                                    <p className="mt-2 text-xs text-muted-foreground">Aguardando conexão...</p>
                                )}
                            </div>
                        )}
                        {!qrCode && !isLoadingQr && (
                            <p className="text-sm text-muted-foreground">Clique "Iniciar Conexão" para gerar o QR Code.</p>
                        )}
                    </div>
                </div>
                <DialogFooter>
                    <Button
                        onClick={handleStartConnection}
                        disabled={isLoadingQr || qrCode !== null}
                    >
                        {isLoadingQr ? 'Gerando...' : 'Iniciar Conexão'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
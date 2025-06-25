// src/components/AuthForm.tsx
'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/hooks/useAuth';
// Se for usar Sonner/Toast:
import Link from 'next/link';

interface AuthFormProps {
    type: 'login' | 'register';
}

export function AuthForm({ type }: AuthFormProps) {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const { handleLogin, handleRegister, loading } = useAuth();
    // Se for usar Sonner/Toast:

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        let result;
        if (type === 'login') {
            result = await handleLogin(username, password);
        } else {
            result = await handleRegister(username, email, password);
        }

        /*// Se for usar Sonner/Toast:
        if (result.success) {
            toast({
                title: type === 'login' ? "Login bem-sucedido!" : "Registro bem-sucedido!",
                description: type === 'login' ? "Você foi logado com sucesso." : "Sua conta foi criada. Faça login para continuar.",
            });
        } else {
            toast({
                title: "Erro!",
                description: result.error || "Ocorreu um erro inesperado.",
                variant: "destructive",
            });
        }*/
    };

    return (
        <Card className="w-[350px]">
            <CardHeader>
                <CardTitle>{type === 'login' ? 'Entrar' : 'Registrar'}</CardTitle>
                <CardDescription>
                    {type === 'login' ? 'Acesse sua conta para gerenciar suas conexões.' : 'Crie uma nova conta para começar a usar.'}
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit}>
                    <div className="grid w-full items-center gap-4">
                        <div className="flex flex-col space-y-1.5">
                            <Label htmlFor="username">Usuário</Label>
                            <Input
                                id="username"
                                placeholder="Seu nome de usuário"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                            />
                        </div>
                        {type === 'register' && (
                            <div className="flex flex-col space-y-1.5">
                                <Label htmlFor="email">Email</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="seu@email.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                />
                            </div>
                        )}
                        <div className="flex flex-col space-y-1.5">
                            <Label htmlFor="password">Senha</Label>
                            <Input
                                id="password"
                                type="password"
                                placeholder="Sua senha secreta"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>
                    </div>
                    <CardFooter className="flex justify-between p-0 pt-6">
                        <Button type="submit" disabled={loading}>
                            {loading ? 'Processando...' : (type === 'login' ? 'Entrar' : 'Registrar')}
                        </Button>
                        {type === 'login' ? (
                            <p className="text-sm text-muted-foreground">
                                Não tem conta? <Link href="/auth?type=register" className="underline">Registre-se</Link>
                            </p>
                        ) : (
                            <p className="text-sm text-muted-foreground">
                                Já tem conta? <Link href="/auth?type=login" className="underline">Entrar</Link>
                            </p>
                        )}
                    </CardFooter>
                </form>
            </CardContent>
        </Card>
    );
}
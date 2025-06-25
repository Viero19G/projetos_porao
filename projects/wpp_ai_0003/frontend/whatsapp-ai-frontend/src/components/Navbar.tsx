// src/components/Navbar.tsx
'use client';

import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { UserCircle2 } from 'lucide-react';

export function Navbar() {
    const { user, handleLogout } = useAuth();

    return (
        <nav className="bg-gray-800 text-white p-4 flex justify-between items-center">
            <Link href="/" className="text-xl font-bold">
                WhatsApp IA Manager
            </Link>
            <div>
                {user?.isAuthenticated ? (
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                                <UserCircle2 className="h-6 w-6" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className="w-56" align="end" forceMount>
                            <DropdownMenuLabel className="font-normal">
                                <div className="flex flex-col space-y-1">
                                    <p className="text-sm font-medium leading-none">Bem-vindo!</p>
                                    <p className="text-xs leading-none text-muted-foreground">
                                        {user.username}
                                    </p>
                                </div>
                            </DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={handleLogout}>
                                Sair
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                ) : (
                    <div className="space-x-4">
                        <Link href="/auth">
                            <Button variant="outline" className="text-gray-800">Entrar / Registrar</Button>
                        </Link>
                    </div>
                )}
            </div>
        </nav>
    );
}
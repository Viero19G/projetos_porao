// src/app/layout.tsx
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/hooks/useAuth';
import { Navbar } from '@/components/Navbar';
// Se for usar Sonner:
import { Toaster } from '@/components/ui/sonner'; // OU, se não for usar, remova esta linha

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
    title: 'WhatsApp IA Manager',
    description: 'Gerencie suas conexões WhatsApp com agentes de IA personalizados.',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <AuthProvider>
                    <Navbar />
                    <main className="container mx-auto p-4">
                        {children}
                    </main>
                    {/* Se for usar Sonner: */}
                    <Toaster />
                </AuthProvider>
            </body>
        </html>
    );
}
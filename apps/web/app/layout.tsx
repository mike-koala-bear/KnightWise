import type { Metadata } from 'next';

import { AuthNav } from '@/components/AuthNav';
import { AuthProvider } from '@/components/AuthProvider';
import { BottomNav } from '@/components/BottomNav';
import './globals.css';

export const metadata: Metadata = {
  title: 'KnightWise',
  description: 'Personalized chess learning powered by Stockfish, Maia-3, and AI coaching.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-kw-bg text-slate-100 antialiased">
        <AuthProvider>
          <header className="sticky top-0 z-40 border-b border-kw-border bg-kw-bg/95 backdrop-blur-sm">
            <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="text-2xl">♞</span>
                <span className="text-lg font-bold tracking-tight text-white">KnightWise</span>
              </div>
              <AuthNav />
            </div>
          </header>
          <main className="pb-nav">
            {children}
          </main>
          <BottomNav />
        </AuthProvider>
      </body>
    </html>
  );
}

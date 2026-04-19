import type { Metadata } from 'next';

import { AuthNav } from '@/components/AuthNav';
import { AuthProvider } from '@/components/AuthProvider';
import './globals.css';

export const metadata: Metadata = {
  title: 'KnightWise',
  description: 'Personalized chess learning. Web-first. Powered by Stockfish 17.1, Maia-3, and GPT-4o-mini.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-galaxy-bg text-slate-100 antialiased">
        <AuthProvider>
          <div className="flex justify-end px-6 pt-4">
            <AuthNav />
          </div>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}

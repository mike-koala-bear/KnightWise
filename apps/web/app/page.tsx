'use client';

import Link from 'next/link';
import { useState } from 'react';

import { DailyProgress } from '@/components/DailyProgress';
import { RatingTracker } from '@/components/RatingTracker';
import { StreakBadge } from '@/components/StreakBadge';
import { SyncButton } from '@/components/SyncButton';

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-8 px-6 py-12">
      <header className="flex flex-col items-center gap-3 text-center">
        <h1 className="text-4xl font-bold tracking-tight">KnightWise</h1>
        <p className="text-sm text-slate-400">
          Personal chess coach · Stockfish 17.1 · Maia-3 · GPT-4o-mini
        </p>
        <StreakBadge userId={1} refreshKey={refreshKey} />
      </header>

      <div className="grid gap-4 sm:grid-cols-2">
        <RatingTracker userId={1} days={7} />
        <DailyProgress userId={1} target={8} refreshKey={refreshKey} />
      </div>

      <SyncButton userId={1} onComplete={() => setRefreshKey((k) => k + 1)} />

      <section className="grid gap-3 sm:grid-cols-3">
        <Link
          href={{ pathname: '/warp' }}
          className="rounded-lg border border-indigo-500/40 bg-indigo-500/10 p-4 transition hover:bg-indigo-500/20"
        >
          <div className="text-xs uppercase tracking-wider text-indigo-300">
            Today
          </div>
          <div className="mt-1 text-lg font-semibold">Daily Warp</div>
          <p className="mt-1 text-xs text-slate-400">
            15 minutes on your #1 weakness.
          </p>
        </Link>
        <Link
          href={{ pathname: '/galaxy' }}
          className="rounded-lg border border-white/10 bg-white/5 p-4 transition hover:bg-white/10"
        >
          <div className="text-xs uppercase tracking-wider text-slate-400">
            Map
          </div>
          <div className="mt-1 text-lg font-semibold">Galaxy Path</div>
          <p className="mt-1 text-xs text-slate-400">
            Browse the full curriculum and jump to any topic.
          </p>
        </Link>
        <Link
          href="/drill"
          className="rounded-lg border border-white/10 bg-white/5 p-4 transition hover:bg-white/10"
        >
          <div className="text-xs uppercase tracking-wider text-slate-400">
            Freeplay
          </div>
          <div className="mt-1 text-lg font-semibold">Drill runner</div>
          <p className="mt-1 text-xs text-slate-400">
            Solve the next SRS-due puzzle.
          </p>
        </Link>
      </section>

      <footer className="text-center text-xs text-slate-500">
        Next.js 16 · React 19 · FastAPI 0.115 · Stockfish 17.1 · Maia-3
      </footer>
    </main>
  );
}

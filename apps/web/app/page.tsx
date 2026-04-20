import Link from 'next/link';

import { Board } from '@/components/Board';
import { STARTING_FEN } from '@knightwise/chess';

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center gap-8 px-6 py-12">
      <header className="text-center">
        <h1 className="text-4xl font-bold tracking-tight">KnightWise</h1>
        <p className="mt-2 text-sm text-slate-400">
          Personal MVP — 10 authored nodes + real drills live in PR #3.
        </p>
      </header>

      <section className="w-full max-w-md">
        <Board fen={STARTING_FEN} />
      </section>

      <nav className="flex gap-3 text-sm">
        <Link
          href="/drill"
          className="rounded-md bg-indigo-500 px-4 py-2 font-semibold text-white hover:bg-indigo-400"
        >
          Start drilling
        </Link>
        <Link
          href="/drill?node=back-rank-basics"
          className="rounded-md border border-white/20 px-4 py-2 font-semibold text-white hover:bg-white/5"
        >
          Back-rank basics →
        </Link>
      </nav>

      <footer className="text-center text-xs text-slate-500">
        Next.js 16 · React 19 · FastAPI 0.115 · Stockfish 17.1 · Maia-3
      </footer>
    </main>
  );
}

import { Board } from '@/components/Board';
import { STARTING_FEN } from '@knightwise/chess';

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center gap-8 px-6 py-12">
      <header className="text-center">
        <h1 className="text-4xl font-bold tracking-tight">KnightWise</h1>
        <p className="mt-2 text-sm text-slate-400">
          Personal MVP scaffold — PR #1. Chess analysis lands in PR #2.
        </p>
      </header>

      <section className="w-full max-w-md">
        <Board fen={STARTING_FEN} />
      </section>

      <footer className="text-center text-xs text-slate-500">
        Next.js 16 · React 19 · FastAPI 0.115 · Stockfish 17.1 · Maia-3
      </footer>
    </main>
  );
}

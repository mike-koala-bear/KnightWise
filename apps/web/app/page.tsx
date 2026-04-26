import type { Route } from 'next';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="mx-auto flex min-h-[calc(100vh-8rem)] max-w-lg flex-col items-center justify-center px-6 py-12 text-center">
      {/* Hero icon */}
      <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-3xl bg-kw-green/20 text-6xl shadow-lg shadow-kw-green/20">
        ♞
      </div>

      <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
        Train like a grandmaster.
      </h1>
      <p className="mt-4 text-lg text-slate-400">
        KnightWise turns your real games into a personalized daily training plan with Stockfish analysis, Maia-3 weakness tagging, and adaptive drills.
      </p>

      {/* Feature pills */}
      <div className="mt-8 flex flex-wrap justify-center gap-2">
        {['Daily Lessons', 'Adaptive Drills', 'Game Analysis', 'Streak Tracking'].map((feat) => (
          <span
            key={feat}
            className="rounded-full border border-kw-border bg-kw-surface px-3 py-1 text-sm font-medium text-slate-300"
          >
            {feat}
          </span>
        ))}
      </div>

      {/* CTAs */}
      <div className="mt-10 flex w-full flex-col gap-3">
        <Link href={'/sign-up' as Route} className="btn-primary w-full text-center">
          Get started — it&apos;s free
        </Link>
        <Link href={'/sign-in' as Route} className="btn-secondary w-full text-center">
          I already have an account
        </Link>
      </div>

      {/* Social proof */}
      <p className="mt-8 text-xs text-slate-600">
        Powered by Stockfish 17.1 · Maia-3 · GPT-4o-mini
      </p>
    </div>
  );
}

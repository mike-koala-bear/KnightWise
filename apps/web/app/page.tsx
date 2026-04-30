import type { Route } from 'next';
import { BarChart2, Brain, Crown, Zap } from 'lucide-react';
import Link from 'next/link';

const FEATURES = [
  { icon: <Zap className="h-5 w-5 text-kw-yellow" />, label: 'Daily Lessons' },
  { icon: <Brain className="h-5 w-5 text-kw-purple" />, label: 'Adaptive Drills' },
  { icon: <BarChart2 className="h-5 w-5 text-kw-blue" />, label: 'Game Analysis' },
  { icon: <Crown className="h-5 w-5 text-kw-green" />, label: 'Streak Tracking' },
];

export default function Home() {
  return (
    <div className="mx-auto flex min-h-[calc(100vh-8rem)] max-w-lg flex-col items-center justify-center px-6 py-12 text-center">
      {/* Hero icon */}
      <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-3xl bg-kw-green/20 shadow-lg shadow-kw-green/20">
        <Crown className="h-12 w-12 text-kw-green fill-kw-green/25" />
      </div>

      <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
        Train like a grandmaster.
      </h1>
      <p className="mt-4 text-lg text-slate-400">
        KnightWise turns your real games into a personalized daily training plan — Stockfish analysis, Maia-3 weakness tagging, and adaptive drills.
      </p>

      {/* Feature pills */}
      <div className="mt-8 flex flex-wrap justify-center gap-2">
        {FEATURES.map(({ icon, label }) => (
          <span key={label} className="inline-flex items-center gap-1.5 rounded-full border border-kw-border bg-kw-surface px-3 py-1.5 text-sm font-medium text-slate-300">
            {icon}
            {label}
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

      <p className="mt-8 text-xs text-slate-600">
        Powered by Stockfish 17.1 · Maia-3 · GPT-4o-mini
      </p>
    </div>
  );
}

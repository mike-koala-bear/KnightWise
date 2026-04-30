'use client';

import { ArrowRight, Map, Swords, Zap } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

import { CoachStatusBadge } from '@/components/CoachStatusBadge';
import { DailyProgress } from '@/components/DailyProgress';
import { OnboardingBanner } from '@/components/OnboardingBanner';
import { RatingTracker } from '@/components/RatingTracker';
import { StreakBadge } from '@/components/StreakBadge';
import { SyncButton } from '@/components/SyncButton';

export function Dashboard() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="mx-auto max-w-lg px-4 py-6 space-y-5">
      {/* Streak + Coach row */}
      <div className="flex items-center justify-between">
        <StreakBadge userId={1} refreshKey={refreshKey} />
        <CoachStatusBadge />
      </div>

      {/* Onboarding banner */}
      <OnboardingBanner userId={1} />

      {/* Daily progress */}
      <DailyProgress userId={1} target={8} refreshKey={refreshKey} />

      {/* Primary CTA – Daily Warp */}
      <Link
        href="/warp"
        className="block rounded-2xl bg-gradient-to-br from-kw-green to-kw-green-dark p-5 shadow-lg shadow-kw-green/20 card-lift"
      >
        <div className="flex items-start justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-green-200/80">
              Today&apos;s Lesson
            </span>
            <h2 className="mt-1 text-2xl font-extrabold text-white">Daily Warp</h2>
            <p className="mt-1 text-sm text-green-100/80">15 minutes on your #1 weakness.</p>
          </div>
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/20">
            <Zap className="h-7 w-7 text-yellow-200 fill-yellow-200/40" />
          </div>
        </div>
        <div className="mt-4 inline-flex items-center gap-2 rounded-xl bg-white/20 px-4 py-2 text-sm font-bold text-white">
          Start lesson <ArrowRight className="h-4 w-4" />
        </div>
      </Link>

      {/* Activity cards grid */}
      <div className="grid grid-cols-2 gap-3">
        <Link
          href="/galaxy"
          className="card-lift flex flex-col gap-3 rounded-2xl border border-kw-border bg-kw-surface p-4"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-kw-purple/20">
            <Map className="h-5 w-5 text-kw-purple" />
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-kw-purple">Map</div>
            <div className="mt-0.5 font-bold text-white">Galaxy Path</div>
            <p className="mt-1 text-xs text-slate-400">Browse the full curriculum.</p>
          </div>
        </Link>

        <Link
          href="/drill"
          className="card-lift flex flex-col gap-3 rounded-2xl border border-kw-border bg-kw-surface p-4"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-kw-blue/20">
            <Swords className="h-5 w-5 text-kw-blue" />
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-kw-blue">Practice</div>
            <div className="mt-0.5 font-bold text-white">Drill Runner</div>
            <p className="mt-1 text-xs text-slate-400">Solve your next SRS puzzle.</p>
          </div>
        </Link>
      </div>

      {/* Rating tracker */}
      <RatingTracker userId={1} days={7} />

      {/* Sync */}
      <SyncButton userId={1} onComplete={() => setRefreshKey((k) => k + 1)} />

      <p className="text-center text-[11px] text-slate-600">
        Stockfish 17.1 · Maia-3 · GPT-4o-mini
      </p>
    </div>
  );
}

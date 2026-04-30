'use client';

import { Brain, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';

import { apiPost } from '@/lib/api';
import type { OnboardingState } from '@/lib/types';

type Props = {
  userId: number;
};

export function OnboardingBanner({ userId }: Props) {
  const [state, setState] = useState<OnboardingState | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await apiPost<OnboardingState>(`/v1/onboarding/start?user_id=${userId}`, {});
        if (!cancelled) setState(r);
      } catch {}
    })();
    return () => { cancelled = true; };
  }, [userId]);

  if (!state || state.completed_at) return null;

  const progress = state.attempts_so_far;
  const max = state.max_attempts ?? 12;
  const pct = Math.round((progress / max) * 100);

  return (
    <Link href="/onboarding" className="card-lift block rounded-2xl border border-kw-purple/40 bg-kw-purple/10 p-4">
      <div className="flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-kw-purple/25">
          <Brain className="h-6 w-6 text-kw-purple" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-bold text-white">Take the skill test</div>
          <p className="mt-0.5 text-xs text-slate-400">
            12 adaptive puzzles → your starting Elo. Takes ~10 minutes.
          </p>
          {progress > 0 && (
            <div className="mt-2">
              <div className="mb-1 text-[10px] text-kw-purple">{progress} / {max} done</div>
              <div className="progress-bar h-2">
                <div className="progress-bar-fill bg-kw-purple" style={{ width: `${pct}%` }} />
              </div>
            </div>
          )}
        </div>
        <ChevronRight className="h-5 w-5 text-kw-purple shrink-0 mt-0.5" />
      </div>
    </Link>
  );
}

'use client';

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
        // POST /onboarding/start is idempotent and returns current state.
        const r = await apiPost<OnboardingState>(
          `/v1/onboarding/start?user_id=${userId}`,
          {},
        );
        if (!cancelled) setState(r);
      } catch {
        // user not yet created or API unreachable — render nothing.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (!state || state.completed_at) return null;

  return (
    <Link
      href={{ pathname: '/onboarding' }}
      className="block rounded-lg border border-indigo-500/40 bg-indigo-500/10 px-4 py-3 text-sm transition hover:bg-indigo-500/20"
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="font-semibold text-indigo-200">
            Take the 10-min skill test
          </div>
          <div className="text-xs text-slate-400">
            Sets your starting Elo so every drill is at the right difficulty.
          </div>
        </div>
        <span className="text-indigo-300">→</span>
      </div>
    </Link>
  );
}

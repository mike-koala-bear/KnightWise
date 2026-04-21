'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import type { StreakOut } from '@/lib/types';

type Props = {
  userId?: number;
  refreshKey?: number;
};

export function StreakBadge({ userId = 1, refreshKey = 0 }: Props) {
  const [data, setData] = useState<StreakOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiGet<StreakOut>(`/v1/streak?user_id=${userId}`)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [userId, refreshKey]);

  if (error) return null;
  if (!data) {
    return (
      <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-400">
        …
      </div>
    );
  }

  const flame = data.current > 0 ? '🔥' : '•';
  const color =
    data.current > 0
      ? 'border-amber-400/40 bg-amber-500/10 text-amber-200'
      : 'border-white/10 bg-white/5 text-slate-400';

  return (
    <div
      data-testid="streak-badge"
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs ${color}`}
      title={
        data.longest > data.current
          ? `Current ${data.current}d · longest ${data.longest}d`
          : undefined
      }
    >
      <span aria-hidden="true">{flame}</span>
      <span>
        <span data-testid="streak-current" className="font-semibold">
          {data.current}
        </span>
        <span className="ml-1">day streak</span>
      </span>
      {data.longest > data.current && (
        <span className="ml-1 text-slate-500">· best {data.longest}</span>
      )}
    </div>
  );
}

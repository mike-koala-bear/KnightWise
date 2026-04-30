'use client';

import { Flame, Snowflake } from 'lucide-react';
import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import type { StreakOut } from '@/lib/types';

type Props = {
  userId?: number;
  refreshKey?: number;
};

export function StreakBadge({ userId = 1, refreshKey = 0 }: Props) {
  const [data, setData] = useState<StreakOut | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiGet<StreakOut>(`/v1/streak?user_id=${userId}`)
      .then((d) => { if (!cancelled) setData(d); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [userId, refreshKey]);

  if (!data) {
    return (
      <div className="flex items-center gap-2 rounded-2xl bg-kw-surface px-4 py-2 animate-pulse">
        <div className="h-8 w-8 rounded-full bg-slate-700" />
        <div className="h-4 w-20 rounded bg-slate-700" />
      </div>
    );
  }

  const hasStreak = data.current > 0;

  return (
    <div
      data-testid="streak-badge"
      className={`flex items-center gap-3 rounded-2xl px-4 py-2 ${
        hasStreak
          ? 'bg-amber-500/15 border border-amber-400/30'
          : 'bg-kw-surface border border-kw-border'
      }`}
      title={data.longest > data.current ? `Best: ${data.longest} days` : undefined}
    >
      {hasStreak
        ? <Flame className="h-8 w-8 text-amber-400 fill-amber-400/30" aria-hidden="true" />
        : <Snowflake className="h-7 w-7 text-slate-500" aria-hidden="true" />
      }
      <div>
        <div className="flex items-baseline gap-1">
          <span
            data-testid="streak-current"
            className={`text-xl font-extrabold ${hasStreak ? 'text-amber-300' : 'text-slate-400'}`}
          >
            {data.current}
          </span>
          <span className={`text-sm font-semibold ${hasStreak ? 'text-amber-400/80' : 'text-slate-500'}`}>
            day streak
          </span>
        </div>
        {data.longest > 0 && (
          <div className="text-[10px] text-slate-500">Best: {data.longest} days</div>
        )}
      </div>
    </div>
  );
}

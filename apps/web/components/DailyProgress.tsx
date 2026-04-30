'use client';

import { CheckCircle2, Target } from 'lucide-react';
import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import type { DailyProgressOut } from '@/lib/types';

type Props = {
  userId?: number;
  target?: number;
  refreshKey?: number;
};

export function DailyProgress({ userId = 1, target = 8, refreshKey = 0 }: Props) {
  const [data, setData] = useState<DailyProgressOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiGet<DailyProgressOut>(`/v1/progress/today?user_id=${userId}&target=${target}`)
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e: unknown) => { if (!cancelled) setError(e instanceof Error ? e.message : String(e)); });
    return () => { cancelled = true; };
  }, [userId, target, refreshKey]);

  if (error) {
    return (
      <div className="rounded-2xl border border-kw-border bg-kw-surface p-4 text-sm text-slate-400">
        Progress unavailable
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-2xl border border-kw-border bg-kw-surface p-4 animate-pulse">
        <div className="h-4 w-32 rounded bg-slate-700 mb-3" />
        <div className="h-4 w-full rounded-full bg-slate-700" />
      </div>
    );
  }

  const pct = Math.min(100, Math.round((data.solved / Math.max(1, data.target)) * 100));

  return (
    <div
      data-testid="daily-progress"
      className={`rounded-2xl border p-4 ${
        data.complete ? 'border-kw-green/40 bg-kw-green/10' : 'border-kw-border bg-kw-surface'
      }`}
    >
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {data.complete
            ? <CheckCircle2 className="h-5 w-5 text-kw-green" />
            : <Target className="h-5 w-5 text-kw-blue" />
          }
          <span className="text-sm font-bold text-white">
            {data.complete ? "Goal complete!" : "Today's goal"}
          </span>
        </div>
        <span className={`text-sm font-extrabold ${data.complete ? 'text-kw-green' : 'text-slate-300'}`}>
          <span data-testid="progress-solved">{data.solved}</span>
          <span className="text-slate-500"> / {data.target}</span>
        </span>
      </div>

      <div className="progress-bar">
        <div
          className={`progress-bar-fill ${data.complete ? 'bg-kw-green' : 'bg-kw-blue'}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {data.attempts > data.solved && (
        <div className="mt-2 text-[11px] text-slate-500">
          {data.attempts - data.solved} incorrect {data.attempts - data.solved === 1 ? 'try' : 'tries'} today
        </div>
      )}
    </div>
  );
}

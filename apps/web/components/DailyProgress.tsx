'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import type { DailyProgressOut } from '@/lib/types';

type Props = {
  userId?: number;
  target?: number;
  /** Bump this to force a refetch after a drill is submitted. */
  refreshKey?: number;
};

export function DailyProgress({ userId = 1, target = 8, refreshKey = 0 }: Props) {
  const [data, setData] = useState<DailyProgressOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiGet<DailyProgressOut>(`/v1/progress/today?user_id=${userId}&target=${target}`)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [userId, target, refreshKey]);

  if (error) {
    return (
      <div className="rounded-lg border border-rose-500/40 bg-rose-500/5 p-4 text-sm text-rose-200">
        Progress unavailable: {error}
      </div>
    );
  }
  if (!data) {
    return (
      <div className="rounded-lg border border-white/10 bg-white/5 p-4 text-sm text-slate-400">
        Loading progress…
      </div>
    );
  }

  const pct = Math.min(1, data.solved / Math.max(1, data.target));
  const ringSize = 64;
  const stroke = 6;
  const radius = (ringSize - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - pct);

  const ringColor = data.complete ? '#34d399' : '#6ae0ff';
  const label = data.complete ? "Today's goal hit" : 'Today';

  return (
    <div
      data-testid="daily-progress"
      className="flex items-center gap-4 rounded-lg border border-white/10 bg-white/5 p-4"
    >
      <svg width={ringSize} height={ringSize} aria-hidden="true">
        <circle
          cx={ringSize / 2}
          cy={ringSize / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={stroke}
        />
        <circle
          cx={ringSize / 2}
          cy={ringSize / 2}
          r={radius}
          fill="none"
          stroke={ringColor}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          transform={`rotate(-90 ${ringSize / 2} ${ringSize / 2})`}
        />
      </svg>
      <div className="flex-1">
        <div className="text-xs uppercase tracking-wider text-slate-400">{label}</div>
        <div className="mt-0.5 text-xl font-semibold">
          <span data-testid="progress-solved">{data.solved}</span>
          <span className="text-slate-500"> / {data.target}</span>
          <span className="ml-2 text-sm font-normal text-slate-400">drills solved</span>
        </div>
        {data.attempts > data.solved && (
          <div className="mt-0.5 text-[11px] text-slate-500">
            {data.attempts - data.solved} incorrect {data.attempts - data.solved === 1 ? 'try' : 'tries'} today
          </div>
        )}
      </div>
    </div>
  );
}

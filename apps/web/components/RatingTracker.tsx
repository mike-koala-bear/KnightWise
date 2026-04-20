'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import type { RatingHistoryOut } from '@/lib/types';

type Props = {
  userId?: number;
  days?: number;
};

export function RatingTracker({ userId = 1, days = 7 }: Props) {
  const [data, setData] = useState<RatingHistoryOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiGet<RatingHistoryOut>(`/v1/rating/history?user_id=${userId}&days=${days}`)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [userId, days]);

  if (error) {
    return (
      <div className="rounded-lg border border-rose-500/40 bg-rose-500/5 p-4 text-sm text-rose-200">
        Rating history unavailable: {error}
      </div>
    );
  }
  if (!data) {
    return (
      <div className="rounded-lg border border-white/10 bg-white/5 p-4 text-sm text-slate-400">
        Loading rating…
      </div>
    );
  }

  const ratings = data.points.map((p) => p.rating);
  const known = ratings.filter((r): r is number => r !== null);
  const min = known.length ? Math.min(...known) : 0;
  const max = known.length ? Math.max(...known) : 1;
  const range = Math.max(1, max - min);

  const width = 320;
  const height = 80;
  const padX = 8;
  const padY = 12;
  const n = data.points.length;

  const coords = data.points.map((p, i) => {
    const x = padX + (i * (width - padX * 2)) / Math.max(1, n - 1);
    if (p.rating === null) return { x, y: null as number | null, rating: null };
    const y = padY + (1 - (p.rating - min) / range) * (height - padY * 2);
    return { x, y, rating: p.rating };
  });

  const path = coords
    .filter((c) => c.y !== null)
    .map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${(c.y as number).toFixed(1)}`)
    .join(' ');

  const deltaLabel =
    data.delta === null
      ? '—'
      : data.delta > 0
        ? `+${data.delta}`
        : `${data.delta}`;

  const deltaColor =
    data.delta === null
      ? 'text-slate-400'
      : data.delta > 0
        ? 'text-emerald-300'
        : data.delta < 0
          ? 'text-rose-300'
          : 'text-slate-300';

  return (
    <div
      data-testid="rating-tracker"
      className="rounded-lg border border-white/10 bg-white/5 p-4"
    >
      <div className="flex items-baseline justify-between">
        <div>
          <div className="text-xs uppercase tracking-wider text-slate-400">Rating</div>
          <div className="text-3xl font-semibold">
            {data.current_rating ?? '—'}
          </div>
        </div>
        <div className={`text-sm font-medium ${deltaColor}`}>
          {deltaLabel} last {data.days}d
        </div>
      </div>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="mt-3 w-full"
        aria-label={`Rating history sparkline for the last ${data.days} days`}
      >
        <path d={path} fill="none" stroke="#6ae0ff" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        {coords.map((c, i) =>
          c.y === null ? null : (
            <circle key={i} cx={c.x} cy={c.y} r={2.5} fill="#6ae0ff" />
          ),
        )}
      </svg>
      <div className="mt-1 flex justify-between text-[10px] text-slate-500">
        <span>{data.points[0]?.day}</span>
        <span>{data.points[n - 1]?.day}</span>
      </div>
    </div>
  );
}

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
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e: unknown) => { if (!cancelled) setError(e instanceof Error ? e.message : String(e)); });
    return () => { cancelled = true; };
  }, [userId, days]);

  if (error) {
    return (
      <div className="rounded-2xl border border-kw-border bg-kw-surface p-4 text-sm text-slate-400">
        Rating unavailable — sync your games to get started.
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-2xl border border-kw-border bg-kw-surface p-4 animate-pulse">
        <div className="h-4 w-24 rounded bg-slate-700 mb-3" />
        <div className="h-16 w-full rounded bg-slate-700" />
      </div>
    );
  }

  const ratings = data.points.map((p) => p.rating);
  const known = ratings.filter((r): r is number => r !== null);
  const min = known.length ? Math.min(...known) : 0;
  const max = known.length ? Math.max(...known) : 1;
  const range = Math.max(1, max - min);

  const width = 300;
  const height = 64;
  const padX = 4;
  const padY = 8;
  const n = data.points.length;

  const coords = data.points.map((p, i) => {
    const x = padX + (i * (width - padX * 2)) / Math.max(1, n - 1);
    if (p.rating === null) return { x, y: null as number | null };
    const y = padY + (1 - (p.rating - min) / range) * (height - padY * 2);
    return { x, y };
  });

  const path = coords
    .filter((c) => c.y !== null)
    .map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${(c.y as number).toFixed(1)}`)
    .join(' ');

  const deltaLabel =
    data.delta === null ? null : data.delta > 0 ? `+${data.delta}` : `${data.delta}`;
  const deltaColor =
    data.delta === null ? '' : data.delta > 0 ? 'text-kw-green' : data.delta < 0 ? 'text-kw-red' : 'text-slate-400';

  return (
    <div
      data-testid="rating-tracker"
      className="rounded-2xl border border-kw-border bg-kw-surface p-4"
    >
      <div className="mb-3 flex items-end justify-between">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-slate-500">Rating</div>
          <div className="text-3xl font-extrabold text-white">
            {data.current_rating ?? '—'}
          </div>
        </div>
        {deltaLabel && (
          <div className={`rounded-xl px-2 py-1 text-sm font-bold ${deltaColor} bg-white/5`}>
            {deltaLabel} <span className="text-slate-500 font-normal text-xs">{data.days}d</span>
          </div>
        )}
      </div>

      {known.length > 1 ? (
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full"
          aria-label={`Rating history for the last ${data.days} days`}
        >
          {/* Area fill */}
          <defs>
            <linearGradient id="ratingGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#58CC02" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#58CC02" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path
            d={`${path} L ${coords.filter(c => c.y !== null).slice(-1)[0]?.x} ${height} L ${coords.filter(c => c.y !== null)[0]?.x} ${height} Z`}
            fill="url(#ratingGrad)"
          />
          <path d={path} fill="none" stroke="#58CC02" strokeWidth={2.5} strokeLinejoin="round" strokeLinecap="round" />
          {coords.map((c, i) =>
            c.y === null ? null : (
              <circle key={i} cx={c.x} cy={c.y} r={3} fill="#58CC02" />
            ),
          )}
        </svg>
      ) : (
        <div className="flex h-16 items-center justify-center text-sm text-slate-500">
          Sync games to see rating history
        </div>
      )}

      {known.length > 1 && (
        <div className="mt-1 flex justify-between text-[10px] text-slate-600">
          <span>{data.points[0]?.day}</span>
          <span>{data.points[n - 1]?.day}</span>
        </div>
      )}
    </div>
  );
}

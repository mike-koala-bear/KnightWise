'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Board } from '@/components/Board';
import { apiGet } from '@/lib/api';
import type { DailyWarpOut } from '@/lib/types';

type Props = {
  userId?: number;
};

export function WarpView({ userId = 1 }: Props) {
  const [warp, setWarp] = useState<DailyWarpOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiGet<DailyWarpOut>(`/v1/warp/today?user_id=${userId}`)
      .then((d) => {
        if (!cancelled) setWarp(d);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (error) {
    return (
      <div className="rounded-lg border border-rose-500/40 bg-rose-500/5 p-4 text-sm text-rose-200">
        Could not load today&apos;s Warp: {error}. Have you seeded the DB and created a user?
      </div>
    );
  }
  if (!warp) {
    return <div className="text-sm text-slate-400">Composing today&apos;s Warp…</div>;
  }

  const firstPuzzle = warp.drill_puzzles[0];

  return (
    <div className="flex w-full flex-col gap-6" data-testid="warp-view">
      <section className="rounded-lg border border-indigo-500/30 bg-indigo-500/5 p-4">
        <div className="text-xs uppercase tracking-wider text-indigo-300">
          Today&apos;s focus
        </div>
        <h2 className="mt-1 text-2xl font-semibold">
          {warp.node_title ?? 'Back-rank basics'}
        </h2>
        <p className="mt-2 text-sm text-slate-200">{warp.coach_note}</p>
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-400">
          <span>
            Top weakness:{' '}
            <code className="rounded bg-black/30 px-1 py-0.5 text-indigo-200">
              {warp.top_weakness_tag ?? 'not enough data'}
            </code>
          </span>
          <span>·</span>
          <span>{warp.games_analyzed} games analyzed</span>
          <span>·</span>
          <span>{warp.drill_puzzles.length} drills queued</span>
        </div>
      </section>

      {firstPuzzle ? (
        <section className="rounded-lg border border-white/10 bg-white/5 p-4">
          <div className="text-xs uppercase tracking-wider text-slate-400">
            First drill preview
          </div>
          <p className="mt-1 text-sm text-slate-300">
            {firstPuzzle.description ?? 'Solve the position.'}
          </p>
          <div className="mt-3 max-w-sm">
            <Board fen={firstPuzzle.fen} />
          </div>
          {warp.node_slug ? (
            <Link
              href={`/drill?node=${warp.node_slug}`}
              className="mt-4 inline-block rounded-md bg-indigo-500 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-400"
            >
              Start today&apos;s Warp →
            </Link>
          ) : null}
        </section>
      ) : (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/5 p-4 text-sm text-amber-200">
          No drills available yet. Run{' '}
          <code className="rounded bg-black/30 px-1">seed-nodes</code> to import the
          starter content.
        </div>
      )}

      {warp.tag_counts.length > 0 ? (
        <section className="rounded-lg border border-white/10 bg-white/5 p-4">
          <div className="text-xs uppercase tracking-wider text-slate-400">
            Weakness breakdown
          </div>
          <ul className="mt-2 flex flex-wrap gap-2">
            {warp.tag_counts.slice(0, 6).map((tc) => (
              <li
                key={tc.tag}
                className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200"
              >
                {tc.tag} <span className="text-slate-400">×{tc.count}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

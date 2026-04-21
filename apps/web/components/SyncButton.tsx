'use client';

import { useEffect, useRef, useState } from 'react';

import { apiGet, apiPost } from '@/lib/api';
import type { SyncStartedResponse, SyncStatusResponse } from '@/lib/types';

type Props = {
  userId?: number;
  maxGames?: number;
  depth?: number;
  onComplete?: (result: SyncStatusResponse) => void;
};

const POLL_INTERVAL_MS = 1500;

export function SyncButton({ userId = 1, maxGames = 10, depth = 14, onComplete }: Props) {
  const [status, setStatus] = useState<SyncStatusResponse | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, []);

  const running = status?.status === 'running' || status?.status === 'pending' || starting;

  async function start() {
    setError(null);
    setStarting(true);
    try {
      const started = await apiPost<SyncStartedResponse>('/v1/sync', {
        user_id: userId,
        max_games: maxGames,
        depth,
        analyze: true,
      });
      poll(started.job_id);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setStarting(false);
    }
  }

  function poll(jobId: string) {
    if (pollRef.current) window.clearInterval(pollRef.current);
    const tick = async () => {
      try {
        const s = await apiGet<SyncStatusResponse>(`/v1/sync/status/${jobId}`);
        setStatus(s);
        if (s.status === 'done' || s.status === 'error') {
          if (pollRef.current) window.clearInterval(pollRef.current);
          pollRef.current = null;
          if (s.status === 'done') onComplete?.(s);
        }
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : String(e));
        if (pollRef.current) window.clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
    void tick();
    pollRef.current = window.setInterval(tick, POLL_INTERVAL_MS);
  }

  const label = starting
    ? 'Starting…'
    : status?.status === 'running' || status?.status === 'pending'
      ? 'Syncing…'
      : status?.status === 'done'
        ? 'Re-sync my games'
        : 'Sync my games';

  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-4" data-testid="sync-button">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-wider text-slate-400">Game data</div>
          <div className="mt-0.5 text-sm font-medium">Pull your latest Lichess + Chess.com games</div>
        </div>
        <button
          type="button"
          onClick={start}
          disabled={running}
          className="rounded-md bg-indigo-500 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-60"
          data-testid="sync-button-cta"
        >
          {label}
        </button>
      </div>

      {error && (
        <div className="mt-3 rounded border border-rose-500/40 bg-rose-500/5 px-3 py-2 text-xs text-rose-200">
          {error}
        </div>
      )}

      {status && (
        <div
          className="mt-3 space-y-1 text-xs text-slate-300"
          data-testid="sync-status"
          data-status={status.status}
        >
          <div className="flex justify-between text-slate-400">
            <span>{status.message}</span>
            <span className="tabular-nums">
              {status.status === 'done' ? 'done' : status.status}
            </span>
          </div>
          <div className="flex justify-between tabular-nums">
            <span>
              Lichess: {status.lichess_inserted} new / {status.lichess_fetched} fetched
            </span>
            <span>
              Chess.com: {status.chesscom_inserted} new / {status.chesscom_fetched} fetched
            </span>
          </div>
          {status.total_games_to_analyze > 0 && (
            <div className="flex justify-between tabular-nums">
              <span>
                Analyzing: {status.games_analyzed} / {status.total_games_to_analyze}
              </span>
              {status.games_failed > 0 && (
                <span className="text-amber-300">{status.games_failed} failed</span>
              )}
            </div>
          )}
          {status.error && (
            <div className="text-rose-300">{status.error}</div>
          )}
        </div>
      )}
    </div>
  );
}

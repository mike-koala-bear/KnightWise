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
    return () => { if (pollRef.current) window.clearInterval(pollRef.current); };
  }, []);

  const running = status?.status === 'running' || status?.status === 'pending' || starting;
  const done = status?.status === 'done';

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

  return (
    <div
      className={`rounded-2xl border p-4 ${done ? 'border-kw-green/30 bg-kw-green/5' : 'border-kw-border bg-kw-surface'}`}
      data-testid="sync-button"
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-kw-blue/20 text-xl">
            {running ? '⏳' : done ? '✅' : '🔄'}
          </div>
          <div>
            <div className="text-sm font-bold text-white">
              {done ? 'Games synced' : 'Sync your games'}
            </div>
            <div className="text-xs text-slate-400">
              Pull from Lichess + Chess.com
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={start}
          disabled={running}
          className={`rounded-xl px-3 py-2 text-xs font-bold transition ${
            running
              ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
              : 'bg-kw-blue text-white hover:brightness-110'
          }`}
          data-testid="sync-button-cta"
        >
          {starting ? 'Starting…' : running ? 'Syncing…' : done ? 'Re-sync' : 'Sync'}
        </button>
      </div>

      {error && (
        <div className="mt-3 rounded-xl border border-kw-red/30 bg-kw-red/10 px-3 py-2 text-xs text-red-300">
          {error}
        </div>
      )}

      {status && (
        <div className="mt-3 space-y-1 text-xs text-slate-400" data-testid="sync-status" data-status={status.status}>
          <div className="flex justify-between">
            <span>{status.message}</span>
            <span className="tabular-nums font-medium">{status.status}</span>
          </div>
          <div className="flex justify-between tabular-nums">
            <span>Lichess: {status.lichess_inserted} new</span>
            <span>Chess.com: {status.chesscom_inserted} new</span>
          </div>
          {status.total_games_to_analyze > 0 && (
            <div className="flex justify-between tabular-nums">
              <span>Analyzing: {status.games_analyzed}/{status.total_games_to_analyze}</span>
              {status.games_failed > 0 && (
                <span className="text-amber-400">{status.games_failed} failed</span>
              )}
            </div>
          )}
          {status.error && <div className="text-kw-red">{status.error}</div>}
        </div>
      )}
    </div>
  );
}

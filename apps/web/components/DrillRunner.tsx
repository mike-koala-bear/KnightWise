'use client';

import { Chess } from 'chess.js';
import { useEffect, useMemo, useState } from 'react';

import { Board } from '@/components/Board';
import { apiGet, apiPost } from '@/lib/api';
import type { AttemptResponse, NextDrillOut } from '@/lib/types';

type Props = {
  nodeSlug?: string;
};

type Status = 'idle' | 'loading' | 'playing' | 'solved' | 'wrong' | 'empty' | 'error';

export function DrillRunner({ nodeSlug }: Props) {
  const [drill, setDrill] = useState<NextDrillOut | null>(null);
  const [status, setStatus] = useState<Status>('loading');
  const [message, setMessage] = useState<string>('');
  const [currentFen, setCurrentFen] = useState<string>('');
  const [startedAt, setStartedAt] = useState<number>(0);
  const [solutionIndex, setSolutionIndex] = useState(0);
  const [streak, setStreak] = useState(0);

  const game = useMemo(() => new Chess(), []);

  useEffect(() => {
    loadNext();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodeSlug]);

  async function loadNext() {
    setStatus('loading');
    try {
      const qs = nodeSlug ? `?node_slug=${encodeURIComponent(nodeSlug)}` : '';
      const next = await apiGet<NextDrillOut>(`/v1/drills/next${qs}`);
      setDrill(next);
      if (!next.puzzle) {
        setStatus('empty');
        return;
      }
      game.load(next.puzzle.fen);
      setCurrentFen(next.puzzle.fen);
      setSolutionIndex(0);
      setStartedAt(Date.now());
      setStatus('playing');
      setMessage(next.puzzle.description ?? 'Find the best move.');
    } catch (e) {
      setStatus('error');
      setMessage(e instanceof Error ? e.message : 'Load failed');
    }
  }

  async function submitAttempt(correct: boolean, timeMs: number) {
    if (!drill?.puzzle) return;
    try {
      await apiPost<AttemptResponse>('/v1/drills/attempt', {
        user_id: 1,
        puzzle_id: drill.puzzle.id,
        correct,
        time_ms: timeMs,
        hints_used: 0,
      });
    } catch { /* non-fatal */ }
  }

  function onMove(from: string, to: string): boolean {
    if (status !== 'playing' || !drill?.puzzle) return false;

    const expected = drill.puzzle.solution_uci[solutionIndex];
    if (!expected) return false;

    const expectedFrom = expected.slice(0, 2);
    const expectedTo = expected.slice(2, 4);
    const promo = expected.slice(4) || undefined;

    if (from !== expectedFrom || to !== expectedTo) {
      setStatus('wrong');
      setMessage(`Not quite — expected ${expectedFrom}→${expectedTo}`);
      setStreak(0);
      void submitAttempt(false, Date.now() - startedAt);
      return false;
    }

    try {
      const moveInput: { from: string; to: string; promotion?: string } = { from, to };
      if (promo) moveInput.promotion = promo;
      game.move(moveInput);
    } catch {
      return false;
    }

    let idx = solutionIndex + 1;
    const solution = drill.puzzle.solution_uci;
    while (idx < solution.length && idx % 2 === 1) {
      const opp = solution[idx];
      if (!opp) break;
      try {
        const oppMove: { from: string; to: string; promotion?: string } = {
          from: opp.slice(0, 2),
          to: opp.slice(2, 4),
        };
        const oppPromo = opp.slice(4) || undefined;
        if (oppPromo) oppMove.promotion = oppPromo;
        game.move(oppMove);
      } catch { break; }
      idx += 1;
    }
    setCurrentFen(game.fen());

    if (idx >= solution.length) {
      setStatus('solved');
      setMessage('Brilliant! Puzzle solved.');
      setStreak((s) => s + 1);
      void submitAttempt(true, Date.now() - startedAt);
    } else {
      setSolutionIndex(idx);
      setMessage('Right move — keep going…');
    }
    return true;
  }

  const orientation = (() => {
    const fen = drill?.puzzle?.fen ?? '';
    if (!fen) return 'white';
    return fen.split(' ')[1] === 'w' ? 'white' : 'black';
  })();

  return (
    <div className="mx-auto max-w-lg space-y-4 px-4 py-6">
      {/* Streak counter */}
      {streak > 0 && (
        <div className="flex justify-center">
          <div className="animate-bounce-in rounded-2xl border border-amber-400/30 bg-amber-500/15 px-4 py-2 text-sm font-bold text-amber-300">
            🔥 {streak} in a row!
          </div>
        </div>
      )}

      {/* Node context */}
      {drill?.node && (
        <div className="rounded-2xl border border-kw-purple/30 bg-kw-purple/10 px-4 py-3">
          <div className="text-xs font-bold uppercase tracking-wider text-kw-purple">
            {drill.node.domain}
          </div>
          <div className="mt-0.5 font-bold text-white">{drill.node.title}</div>
          {drill.node.description && (
            <p className="mt-1 text-xs text-slate-400">{drill.node.description}</p>
          )}
        </div>
      )}

      {/* Prompt */}
      {status === 'playing' && (
        <div className="rounded-2xl border border-kw-border bg-kw-surface px-4 py-3 text-center">
          <p className="font-semibold text-white">{message}</p>
          <p className="mt-1 text-xs text-slate-500">
            {orientation === 'white' ? 'White' : 'Black'} to move
            {drill?.puzzle && (
              <span className="ml-2 text-slate-600">· rating {drill.puzzle.rating}</span>
            )}
          </p>
        </div>
      )}

      {/* Board */}
      {drill?.puzzle && currentFen && status !== 'empty' && (
        <div className="overflow-hidden rounded-2xl shadow-xl">
          <Board fen={currentFen} orientation={orientation} onMove={onMove} id="drill-board" />
        </div>
      )}

      {/* Feedback */}
      {(status === 'solved' || status === 'wrong') && (
        <div
          className={`animate-slide-up rounded-2xl border p-4 ${
            status === 'solved'
              ? 'border-kw-green/40 bg-kw-green/10'
              : 'border-kw-red/40 bg-kw-red/10'
          }`}
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">{status === 'solved' ? '🎉' : '💡'}</span>
            <div>
              <div className={`font-bold ${status === 'solved' ? 'text-kw-green' : 'text-kw-red'}`}>
                {status === 'solved' ? 'Correct!' : 'Wrong move'}
              </div>
              <div className="text-sm text-slate-300">{message}</div>
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {status === 'empty' && (
        <div className="rounded-2xl border border-kw-border bg-kw-surface p-8 text-center">
          <div className="text-4xl mb-3">♟️</div>
          <div className="font-bold text-white">No drills available yet</div>
          <p className="mt-2 text-sm text-slate-400">
            Sync your games first — KnightWise will generate drills from your actual weaknesses.
          </p>
        </div>
      )}

      {/* Error state */}
      {status === 'error' && (
        <div className="rounded-2xl border border-kw-red/30 bg-kw-red/10 p-4 text-center text-sm text-slate-300">
          {message}
        </div>
      )}

      {/* Continue button */}
      {(status === 'solved' || status === 'wrong' || status === 'empty' || status === 'error') && (
        <button type="button" onClick={loadNext} className="btn-primary w-full">
          {status === 'solved' ? 'Next puzzle →' : status === 'wrong' ? 'Try another' : 'Retry'}
        </button>
      )}
    </div>
  );
}

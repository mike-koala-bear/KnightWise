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
  const [message, setMessage] = useState<string>('Loading drill…');
  const [currentFen, setCurrentFen] = useState<string>('');
  const [startedAt, setStartedAt] = useState<number>(0);
  const [solutionIndex, setSolutionIndex] = useState(0);

  const game = useMemo(() => new Chess(), []);

  useEffect(() => {
    loadNext();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodeSlug]);

  async function loadNext() {
    setStatus('loading');
    setMessage('Loading drill…');
    try {
      const qs = nodeSlug ? `?node_slug=${encodeURIComponent(nodeSlug)}` : '';
      const next = await apiGet<NextDrillOut>(`/v1/drills/next${qs}`);
      setDrill(next);
      if (!next.puzzle) {
        setStatus('empty');
        setMessage('No drills available. Run `cli seed-nodes` first.');
        return;
      }
      game.load(next.puzzle.fen);
      setCurrentFen(next.puzzle.fen);
      setSolutionIndex(0);
      setStartedAt(Date.now());
      setStatus('playing');
      setMessage(next.puzzle.description ?? 'Your move.');
    } catch (e) {
      setStatus('error');
      setMessage(e instanceof Error ? e.message : 'Load failed');
    }
  }

  async function submitAttempt(correct: boolean, timeMs: number, hintsUsed = 0) {
    if (!drill?.puzzle) return;
    try {
      await apiPost<AttemptResponse>('/v1/drills/attempt', {
        user_id: 1,
        puzzle_id: drill.puzzle.id,
        correct,
        time_ms: timeMs,
        hints_used: hintsUsed,
      });
    } catch {
      // non-fatal; local UI still works
    }
  }

  function onMove(from: string, to: string): boolean {
    if (status !== 'playing' || !drill?.puzzle) return false;

    const expected = drill.puzzle.solution_uci[solutionIndex];
    if (!expected) return false;

    const [expectedFrom, expectedTo, promo] = [
      expected.slice(0, 2),
      expected.slice(2, 4),
      expected.slice(4) || undefined,
    ];

    if (from !== expectedFrom || to !== expectedTo) {
      setStatus('wrong');
      setMessage(`Not quite — expected ${expectedFrom}→${expectedTo}. Try the next one.`);
      submitAttempt(false, Date.now() - startedAt);
      return false;
    }

    try {
      const moveInput: { from: string; to: string; promotion?: string } = { from, to };
      if (promo) moveInput.promotion = promo;
      game.move(moveInput);
    } catch {
      return false;
    }
    setCurrentFen(game.fen());

    const nextIdx = solutionIndex + 1;
    if (nextIdx >= drill.puzzle.solution_uci.length) {
      setStatus('solved');
      setMessage('Solved!');
      submitAttempt(true, Date.now() - startedAt);
    } else {
      setSolutionIndex(nextIdx);
      setMessage('Right. Keep going…');
    }
    return true;
  }

  const orientation = (() => {
    if (!currentFen) return 'white';
    const parts = currentFen.split(' ');
    return parts[1] === 'w' ? 'white' : 'black';
  })();

  return (
    <section className="w-full max-w-md space-y-4">
      {drill?.node && (
        <div className="rounded-lg border border-white/10 bg-slate-900/60 p-4 text-sm">
          <div className="font-semibold">{drill.node.title}</div>
          {drill.node.description && (
            <p className="mt-1 text-slate-400">{drill.node.description}</p>
          )}
        </div>
      )}

      {drill?.puzzle && currentFen && (
        <Board fen={currentFen} orientation={orientation} onMove={onMove} id="drill-board" />
      )}

      <div className="rounded-lg border border-white/10 bg-slate-900/40 p-3 text-sm">
        <div>{message}</div>
        {drill?.puzzle && (
          <div className="mt-1 text-xs text-slate-500">
            puzzle #{drill.puzzle.id} · rating {drill.puzzle.rating}
            {drill.puzzle.themes.length > 0 && ` · ${drill.puzzle.themes.join(', ')}`}
          </div>
        )}
      </div>

      {(status === 'solved' || status === 'wrong' || status === 'empty' || status === 'error') && (
        <button
          type="button"
          onClick={loadNext}
          className="w-full rounded-md bg-indigo-500 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-400"
        >
          Next drill
        </button>
      )}
    </section>
  );
}

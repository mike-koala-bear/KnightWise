'use client';

import { Chess } from 'chess.js';
import { ArrowRight, CheckCircle2, Crown, Flame, Lightbulb, RefreshCw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { Board } from '@/components/Board';
import { apiGet, apiPost } from '@/lib/api';
import type { AttemptResponse, NextDrillOut } from '@/lib/types';

type Props = { nodeSlug?: string };
type Status = 'idle' | 'loading' | 'playing' | 'solved' | 'wrong' | 'empty' | 'error';

export function DrillRunner({ nodeSlug }: Props) {
  const [drill, setDrill] = useState<NextDrillOut | null>(null);
  const [status, setStatus] = useState<Status>('loading');
  const [message, setMessage] = useState('');
  const [currentFen, setCurrentFen] = useState('');
  const [startedAt, setStartedAt] = useState(0);
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
      if (!next.puzzle) { setStatus('empty'); return; }
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
        user_id: 1, puzzle_id: drill.puzzle.id, correct, time_ms: timeMs, hints_used: 0,
      });
    } catch {}
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
      setMessage(`Expected ${expectedFrom}→${expectedTo}`);
      setStreak(0);
      void submitAttempt(false, Date.now() - startedAt);
      return false;
    }

    try {
      const mv: { from: string; to: string; promotion?: string } = { from, to };
      if (promo) mv.promotion = promo;
      game.move(mv);
    } catch { return false; }

    let idx = solutionIndex + 1;
    const solution = drill.puzzle.solution_uci;
    while (idx < solution.length && idx % 2 === 1) {
      const opp = solution[idx];
      if (!opp) break;
      try {
        const oppMv: { from: string; to: string; promotion?: string } = { from: opp.slice(0, 2), to: opp.slice(2, 4) };
        const oppPromo = opp.slice(4) || undefined;
        if (oppPromo) oppMv.promotion = oppPromo;
        game.move(oppMv);
      } catch { break; }
      idx += 1;
    }
    setCurrentFen(game.fen());

    if (idx >= solution.length) {
      setStatus('solved');
      setMessage('Puzzle solved!');
      setStreak((s) => s + 1);
      void submitAttempt(true, Date.now() - startedAt);
    } else {
      setSolutionIndex(idx);
      setMessage('Right — keep going…');
    }
    return true;
  }

  const orientation = (() => {
    const fen = drill?.puzzle?.fen ?? '';
    return !fen ? 'white' : fen.split(' ')[1] === 'w' ? 'white' : 'black';
  })();

  return (
    <div className="mx-auto max-w-lg space-y-4 px-4 py-6">
      {/* Streak */}
      {streak > 0 && (
        <div className="flex justify-center">
          <div className="animate-bounce-in inline-flex items-center gap-2 rounded-2xl border border-amber-400/30 bg-amber-500/15 px-4 py-2 text-sm font-bold text-amber-300">
            <Flame className="h-4 w-4 text-amber-400 fill-amber-400/40" />
            {streak} in a row!
          </div>
        </div>
      )}

      {/* Node context */}
      {drill?.node && (
        <div className="rounded-2xl border border-kw-purple/30 bg-kw-purple/10 px-4 py-3">
          <div className="text-xs font-bold uppercase tracking-wider text-kw-purple">{drill.node.domain}</div>
          <div className="mt-0.5 font-bold text-white">{drill.node.title}</div>
          {drill.node.description && <p className="mt-1 text-xs text-slate-400">{drill.node.description}</p>}
        </div>
      )}

      {/* Prompt */}
      {status === 'playing' && (
        <div className="rounded-2xl border border-kw-border bg-kw-surface px-4 py-3 text-center">
          <p className="font-semibold text-white">{message}</p>
          <p className="mt-1 text-xs text-slate-500">
            {orientation === 'white' ? 'White' : 'Black'} to move
            {drill?.puzzle && <span className="ml-2 text-slate-600">· rating {drill.puzzle.rating}</span>}
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
        <div className={`animate-slide-up rounded-2xl border p-4 ${status === 'solved' ? 'border-kw-green/40 bg-kw-green/10' : 'border-kw-red/40 bg-kw-red/10'}`}>
          <div className="flex items-center gap-3">
            {status === 'solved'
              ? <CheckCircle2 className="h-6 w-6 text-kw-green shrink-0" />
              : <Lightbulb className="h-6 w-6 text-amber-400 shrink-0" />
            }
            <div>
              <div className={`font-bold ${status === 'solved' ? 'text-kw-green' : 'text-kw-red'}`}>
                {status === 'solved' ? 'Correct!' : 'Wrong move'}
              </div>
              <div className="text-sm text-slate-300">{message}</div>
            </div>
          </div>
        </div>
      )}

      {/* Empty */}
      {status === 'empty' && (
        <div className="rounded-2xl border border-kw-border bg-kw-surface p-8 text-center">
          <div className="flex justify-center mb-3">
            <Crown className="h-12 w-12 text-slate-600" />
          </div>
          <div className="font-bold text-white">No drills available yet</div>
          <p className="mt-2 text-sm text-slate-400">Sync your games — KnightWise generates drills from your actual weaknesses.</p>
        </div>
      )}

      {/* Error */}
      {status === 'error' && (
        <div className="rounded-2xl border border-kw-red/30 bg-kw-red/10 p-4 text-center text-sm text-slate-300">{message}</div>
      )}

      {/* Action button */}
      {(status === 'solved' || status === 'wrong' || status === 'empty' || status === 'error') && (
        <button type="button" onClick={loadNext} className="btn-primary w-full">
          {status === 'solved'
            ? <><span>Next puzzle</span><ArrowRight className="h-4 w-4" /></>
            : status === 'wrong'
              ? <><span>Try another</span><RefreshCw className="h-4 w-4" /></>
              : <><span>Retry</span><RefreshCw className="h-4 w-4" /></>
          }
        </button>
      )}
    </div>
  );
}

'use client';

import { Chess } from 'chess.js';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { Board } from '@/components/Board';
import { apiGet, apiPost } from '@/lib/api';
import type {
  OnboardingAttemptOut,
  OnboardingNextOut,
  OnboardingState,
} from '@/lib/types';

type Status = 'loading' | 'playing' | 'feedback' | 'done' | 'error';

type Props = {
  userId: number;
};

export function OnboardingRunner({ userId }: Props) {
  const router = useRouter();
  const [next, setNext] = useState<OnboardingNextOut | null>(null);
  const [status, setStatus] = useState<Status>('loading');
  const [message, setMessage] = useState<string>('Loading skill test…');
  const [lastAttempt, setLastAttempt] = useState<OnboardingAttemptOut | null>(null);
  const [startedAt, setStartedAt] = useState<number>(0);

  const game = useMemo(() => new Chess(), []);

  const loadNext = useCallback(async () => {
    setStatus('loading');
    setLastAttempt(null);
    try {
      const r = await apiGet<OnboardingNextOut>(
        `/v1/onboarding/next?user_id=${userId}`,
      );
      setNext(r);
      if (r.done || !r.puzzle) {
        setStatus('done');
        setMessage('Skill test complete.');
        return;
      }
      game.load(r.puzzle.fen);
      setStartedAt(Date.now());
      setStatus('playing');
      setMessage(r.puzzle.description ?? 'Find the best move.');
    } catch (e) {
      setStatus('error');
      setMessage(e instanceof Error ? e.message : 'Failed to load.');
    }
  }, [userId, game]);

  useEffect(() => {
    (async () => {
      try {
        await apiPost<OnboardingState>(
          `/v1/onboarding/start?user_id=${userId}`,
          {},
        );
      } catch (e) {
        setStatus('error');
        setMessage(e instanceof Error ? e.message : 'Failed to start.');
        return;
      }
      await loadNext();
    })();
  }, [userId, loadNext]);

  async function submit(moveUci: string) {
    if (!next?.puzzle) return;
    setStatus('feedback');
    try {
      const r = await apiPost<OnboardingAttemptOut>('/v1/onboarding/attempt', {
        user_id: userId,
        puzzle_id: next.puzzle.id,
        move_uci: moveUci,
        time_ms: Date.now() - startedAt,
      });
      setLastAttempt(r);
      setMessage(
        r.correct
          ? 'Correct.'
          : `Not quite. Expected ${r.expected_uci}.`,
      );
      if (r.done) {
        setStatus('done');
      }
    } catch (e) {
      setStatus('error');
      setMessage(e instanceof Error ? e.message : 'Attempt failed.');
    }
  }

  function onMove(from: string, to: string): boolean {
    if (status !== 'playing') return false;
    let promo: string | undefined;
    try {
      const move = game.move({ from, to, promotion: 'q' });
      if (!move) return false;
      if (move.promotion) promo = move.promotion;
    } catch {
      return false;
    }
    const uci = `${from}${to}${promo ?? ''}`;
    void submit(uci);
    return true;
  }

  async function finish() {
    try {
      await apiPost<OnboardingState>('/v1/onboarding/finish', {
        user_id: userId,
      });
    } catch {
      // non-fatal: state is already terminal locally
    }
    router.push('/');
    router.refresh();
  }

  const orientation = (() => {
    const fen = next?.puzzle?.fen ?? '';
    if (!fen) return 'white';
    return fen.split(' ')[1] === 'w' ? 'white' : 'black';
  })();

  // lastAttempt holds the post-attempt state; next holds pre-attempt. Prefer post.
  const state: OnboardingState | null = lastAttempt?.state ?? next?.state ?? null;
  const muRounded = state ? Math.round(state.rating_mu) : 1500;
  const sigmaRounded = state ? Math.round(state.rating_sigma) : 350;
  const attempts = state?.attempts_so_far ?? 0;
  const maxAttempts = state?.max_attempts ?? 12;

  return (
    <section className="w-full max-w-md space-y-4">
      <div className="rounded-lg border border-indigo-500/40 bg-indigo-500/10 p-4 text-sm">
        <div className="font-semibold">Calibrating your starting Elo</div>
        <p className="mt-1 text-slate-300">
          12 adaptive puzzles. We pick each one based on how you did on the last,
          then estimate your rating with Glicko-1.
        </p>
        <div className="mt-2 flex gap-4 text-xs text-slate-400">
          <span>
            Estimate <span className="font-mono text-slate-200">{muRounded}</span>{' '}
            <span className="text-slate-500">±{sigmaRounded}</span>
          </span>
          <span>
            Question{' '}
            <span className="font-mono text-slate-200">
              {Math.min(attempts + (status === 'playing' ? 1 : 0), maxAttempts)}
            </span>{' '}
            / {maxAttempts}
          </span>
        </div>
      </div>

      {next?.puzzle && status !== 'done' && (
        <Board
          fen={game.fen() || next.puzzle.fen}
          orientation={orientation}
          onMove={onMove}
          id="onboarding-board"
        />
      )}

      <div className="rounded-lg border border-white/10 bg-slate-900/40 p-3 text-sm">
        <div>{message}</div>
        {next?.puzzle && status === 'playing' && (
          <div className="mt-1 text-xs text-slate-500">
            puzzle #{next.puzzle.id} · rating {next.puzzle.rating}
          </div>
        )}
      </div>

      {status === 'feedback' && (
        <button
          type="button"
          onClick={loadNext}
          className="w-full rounded-md bg-indigo-500 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-400"
        >
          Next puzzle
        </button>
      )}

      {status === 'done' && (
        <div className="space-y-3">
          <div className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-4 text-sm">
            <div className="font-semibold">Calibration complete.</div>
            <p className="mt-1 text-slate-300">
              Starting Elo:{' '}
              <span className="font-mono text-slate-100">{muRounded}</span>{' '}
              <span className="text-slate-500">(±{sigmaRounded})</span>
            </p>
          </div>
          <button
            type="button"
            onClick={finish}
            className="w-full rounded-md bg-emerald-500 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-400"
          >
            Continue to KnightWise
          </button>
        </div>
      )}

      {status === 'error' && (
        <button
          type="button"
          onClick={loadNext}
          className="w-full rounded-md bg-red-500/80 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500"
        >
          Retry
        </button>
      )}
    </section>
  );
}

'use client';

import { Chess } from 'chess.js';
import { ArrowRight, CheckCircle2, Lightbulb, Trophy, X } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { Board } from '@/components/Board';
import { apiGet, apiPost } from '@/lib/api';
import type { OnboardingAttemptOut, OnboardingNextOut, OnboardingState } from '@/lib/types';

type Status = 'loading' | 'playing' | 'feedback' | 'done' | 'error';
type FeedbackKind = 'correct' | 'wrong' | null;

type Props = { userId: number };

export function OnboardingRunner({ userId }: Props) {
  const router = useRouter();
  const [next, setNext] = useState<OnboardingNextOut | null>(null);
  const [status, setStatus] = useState<Status>('loading');
  const [message, setMessage] = useState('');
  const [lastAttempt, setLastAttempt] = useState<OnboardingAttemptOut | null>(null);
  const [startedAt, setStartedAt] = useState(0);
  const [feedback, setFeedback] = useState<FeedbackKind>(null);

  const game = useMemo(() => new Chess(), []);

  const loadNext = useCallback(async () => {
    setStatus('loading');
    setLastAttempt(null);
    setFeedback(null);
    try {
      const r = await apiGet<OnboardingNextOut>(`/v1/onboarding/next?user_id=${userId}`);
      setNext(r);
      if (r.done || !r.puzzle) { setStatus('done'); return; }
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
        await apiPost<OnboardingState>(`/v1/onboarding/start?user_id=${userId}`, {});
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
      setFeedback(r.correct ? 'correct' : 'wrong');
      setMessage(r.correct ? 'Excellent!' : `Not quite — expected ${r.expected_uci}`);
      if (r.done) setStatus('done');
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
    } catch { return false; }
    void submit(`${from}${to}${promo ?? ''}`);
    return true;
  }

  async function finish() {
    try { await apiPost<OnboardingState>('/v1/onboarding/finish', { user_id: userId }); } catch {}
    router.push('/app');
    router.refresh();
  }

  const orientation = (() => {
    const fen = next?.puzzle?.fen ?? '';
    return !fen ? 'white' : fen.split(' ')[1] === 'w' ? 'white' : 'black';
  })();

  const state: OnboardingState | null = lastAttempt?.state ?? next?.state ?? null;
  const muRounded = state ? Math.round(state.rating_mu) : 1500;
  const attempts = state?.attempts_so_far ?? 0;
  const maxAttempts = state?.max_attempts ?? 12;
  const progressPct = Math.round((attempts / maxAttempts) * 100);

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-4 px-4 py-6">
      {/* Progress header */}
      <div className="flex items-center gap-3">
        <button type="button" onClick={() => router.push('/app')} className="text-slate-400 hover:text-white transition-colors" aria-label="Exit">
          <X className="h-5 w-5" />
        </button>
        <div className="flex-1">
          <div className="progress-bar">
            <div className="progress-bar-fill bg-kw-purple" style={{ width: `${progressPct}%` }} />
          </div>
        </div>
        <div className="text-xs font-bold text-slate-400 tabular-nums">
          {Math.min(attempts + (status === 'playing' ? 1 : 0), maxAttempts)}/{maxAttempts}
        </div>
      </div>

      {/* Rating estimate */}
      <div className="flex justify-center">
        <div className="rounded-2xl border border-kw-purple/30 bg-kw-purple/10 px-4 py-2 text-center">
          <div className="text-xs font-bold uppercase tracking-wider text-kw-purple">Skill Calibration</div>
          <div className="mt-0.5 text-sm text-slate-300">
            Estimated Elo: <span className="font-extrabold text-white">{muRounded}</span>
          </div>
        </div>
      </div>

      {/* Prompt */}
      {status === 'playing' && (
        <div className="rounded-2xl border border-kw-border bg-kw-surface px-4 py-3 text-center">
          <p className="font-semibold text-white">{message}</p>
          <p className="mt-1 text-xs text-slate-500">{orientation === 'white' ? 'White' : 'Black'} to move</p>
        </div>
      )}

      {/* Board */}
      {next?.puzzle && status !== 'done' && status !== 'error' && (
        <div className="rounded-2xl overflow-hidden shadow-xl">
          <Board fen={game.fen() || next.puzzle.fen} orientation={orientation} onMove={onMove} id="onboarding-board" />
        </div>
      )}

      {/* Feedback */}
      {status === 'feedback' && feedback && (
        <div className={`animate-slide-up rounded-2xl border p-4 ${feedback === 'correct' ? 'border-kw-green/40 bg-kw-green/10' : 'border-kw-red/40 bg-kw-red/10'}`}>
          <div className="flex items-center gap-3">
            {feedback === 'correct'
              ? <CheckCircle2 className="h-6 w-6 text-kw-green shrink-0" />
              : <Lightbulb className="h-6 w-6 text-amber-400 shrink-0" />
            }
            <div>
              <div className={`font-bold ${feedback === 'correct' ? 'text-kw-green' : 'text-kw-red'}`}>
                {feedback === 'correct' ? 'Correct!' : 'Not quite'}
              </div>
              <div className="text-sm text-slate-300">{message}</div>
            </div>
          </div>
        </div>
      )}

      {status === 'feedback' && !lastAttempt?.done && (
        <button type="button" onClick={loadNext} className="btn-primary w-full">
          Continue <ArrowRight className="h-4 w-4" />
        </button>
      )}

      {/* Done */}
      {(status === 'done' || (status === 'feedback' && lastAttempt?.done)) && (
        <div className="animate-bounce-in space-y-4">
          <div className="rounded-2xl border border-kw-green/40 bg-kw-green/10 p-5 text-center">
            <div className="flex justify-center mb-3">
              <Trophy className="h-12 w-12 text-kw-yellow fill-kw-yellow/20" />
            </div>
            <div className="text-lg font-extrabold text-white">Calibration complete!</div>
            <p className="mt-2 text-slate-300">
              Your starting Elo: <span className="font-extrabold text-kw-green text-2xl">{muRounded}</span>
            </p>
            <p className="mt-1 text-sm text-slate-400">Every drill will now be tuned to your level.</p>
          </div>
          <button type="button" onClick={finish} className="btn-primary w-full">
            Start training <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Error */}
      {status === 'error' && (
        <div className="space-y-3">
          <div className="rounded-2xl border border-kw-red/40 bg-kw-red/10 p-4 text-center text-sm text-slate-300">{message}</div>
          <button type="button" onClick={loadNext} className="btn-primary w-full">Retry</button>
        </div>
      )}
    </div>
  );
}

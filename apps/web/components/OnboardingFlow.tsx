'use client';

import {
  ArrowRight,
  CheckCircle2,
  Crown,
  Loader2,
  RefreshCw,
  Swords,
  Trophy,
  TrendingUp,
  User,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';

import { apiPost } from '@/lib/api';
import type { OnboardingSetupOut, OnboardingState, SyncStartedResponse, SyncStatusResponse } from '@/lib/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const POLL_MS = 1500;
const MAX_GAMES = 50;

type Step = 'welcome' | 'platforms' | 'syncing' | 'done';
type Platform = 'lichess' | 'chesscom';

function apiGet<T>(path: string): Promise<T> {
  return fetch(`${API_URL}${path}`, { cache: 'no-store' }).then((r) => {
    if (!r.ok) throw new Error(`${path} failed: ${r.status}`);
    return r.json() as Promise<T>;
  });
}

export function OnboardingFlow() {
  const router = useRouter();
  const [step, setStep] = useState<Step>('welcome');
  const [platforms, setPlatforms] = useState<Set<Platform>>(new Set());
  const [lichessUser, setLichessUser] = useState('');
  const [chesscomUser, setChesscomUser] = useState('');
  const [formError, setFormError] = useState('');
  const [syncStatus, setSyncStatus] = useState<SyncStatusResponse | null>(null);
  const [syncError, setSyncError] = useState('');
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function togglePlatform(p: Platform) {
    setPlatforms((prev) => {
      const next = new Set(prev);
      if (next.has(p)) next.delete(p); else next.add(p);
      return next;
    });
  }

  async function startImport() {
    setFormError('');
    const lichess = platforms.has('lichess') ? lichessUser.trim() : '';
    const chesscom = platforms.has('chesscom') ? chesscomUser.trim() : '';

    if (!lichess && !chesscom) {
      setFormError('Select at least one platform and enter your username.');
      return;
    }
    if (platforms.has('lichess') && !lichess) {
      setFormError('Enter your Lichess username.');
      return;
    }
    if (platforms.has('chesscom') && !chesscom) {
      setFormError('Enter your Chess.com username.');
      return;
    }

    setStep('syncing');

    try {
      // Save usernames to user profile
      await apiPost<OnboardingSetupOut>('/v1/onboarding/setup', {
        user_id: 1,
        lichess_username: lichess || null,
        chesscom_username: chesscom || null,
      });

      // Start sync job with analysis
      const started = await apiPost<SyncStartedResponse>('/v1/sync', {
        user_id: 1,
        lichess_username: lichess || null,
        chesscom_username: chesscom || null,
        max_games: MAX_GAMES,
        analyze: true,
        depth: 14,
      });

      pollSync(started.job_id);
    } catch (e) {
      setSyncError(e instanceof Error ? e.message : 'Something went wrong. Try again.');
    }
  }

  function pollSync(jobId: string) {
    if (pollRef.current) clearInterval(pollRef.current);

    const tick = async () => {
      try {
        const s = await apiGet<SyncStatusResponse>(`/v1/sync/status/${jobId}`);
        setSyncStatus(s);
        if (s.status === 'done' || s.status === 'error') {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          if (s.status === 'done') {
            await finishOnboarding();
          } else {
            setSyncError(s.error ?? 'Sync failed.');
          }
        }
      } catch (e) {
        if (pollRef.current) clearInterval(pollRef.current);
        pollRef.current = null;
        setSyncError(e instanceof Error ? e.message : 'Polling failed.');
      }
    };

    void tick();
    pollRef.current = setInterval(tick, POLL_MS);
  }

  async function finishOnboarding() {
    await apiPost<OnboardingState>('/v1/onboarding/complete', { user_id: 1 });
    setStep('done');
  }

  function goToDashboard() {
    router.push('/app');
    router.refresh();
  }

  const totalFetched = syncStatus
    ? (syncStatus.lichess_fetched + syncStatus.chesscom_fetched)
    : 0;
  const analyzedGames = syncStatus?.games_analyzed ?? 0;

  return (
    <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-lg flex-col items-center justify-center px-4 py-8">

      {/* ── WELCOME ── */}
      {step === 'welcome' && (
        <div className="animate-slide-up w-full space-y-8 text-center">
          <div className="flex justify-center">
            <div className="flex h-24 w-24 items-center justify-center rounded-3xl bg-kw-green/20 shadow-xl shadow-kw-green/10">
              <Crown className="h-14 w-14 text-kw-green fill-kw-green/25" />
            </div>
          </div>
          <div>
            <h1 className="text-3xl font-extrabold text-white">Welcome to KnightWise</h1>
            <p className="mt-3 text-base text-slate-400">
              We'll import your real games and build a personalized training plan around your actual weaknesses — not generic puzzles.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {[
              { icon: <TrendingUp className="h-5 w-5 text-kw-green" />, label: 'Game analysis' },
              { icon: <Swords className="h-5 w-5 text-kw-blue" />, label: 'Personal drills' },
              { icon: <Trophy className="h-5 w-5 text-kw-yellow" />, label: 'Weakness fix' },
            ].map(({ icon, label }) => (
              <div key={label} className="flex flex-col items-center gap-2 rounded-2xl border border-kw-border bg-kw-surface p-3">
                {icon}
                <span className="text-xs font-semibold text-slate-300">{label}</span>
              </div>
            ))}
          </div>
          <button onClick={() => setStep('platforms')} className="btn-primary w-full">
            Get started <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* ── PLATFORMS ── */}
      {step === 'platforms' && (
        <div className="animate-slide-up w-full space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-extrabold text-white">Where do you play?</h2>
            <p className="mt-2 text-sm text-slate-400">Select your platforms. We'll import your last {MAX_GAMES} games.</p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {/* Lichess */}
            <button
              type="button"
              onClick={() => togglePlatform('lichess')}
              className={`flex flex-col items-center gap-3 rounded-2xl border p-4 transition-all ${
                platforms.has('lichess')
                  ? 'border-kw-green/60 bg-kw-green/10 ring-1 ring-kw-green/40'
                  : 'border-kw-border bg-kw-surface hover:border-slate-500'
              }`}
            >
              {platforms.has('lichess') && (
                <CheckCircle2 className="h-4 w-4 text-kw-green self-end -mb-2" />
              )}
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-700">
                <span className="text-2xl font-black text-white">L</span>
              </div>
              <span className="font-bold text-white">Lichess</span>
              <span className="text-xs text-slate-400">lichess.org</span>
            </button>

            {/* Chess.com */}
            <button
              type="button"
              onClick={() => togglePlatform('chesscom')}
              className={`flex flex-col items-center gap-3 rounded-2xl border p-4 transition-all ${
                platforms.has('chesscom')
                  ? 'border-kw-green/60 bg-kw-green/10 ring-1 ring-kw-green/40'
                  : 'border-kw-border bg-kw-surface hover:border-slate-500'
              }`}
            >
              {platforms.has('chesscom') && (
                <CheckCircle2 className="h-4 w-4 text-kw-green self-end -mb-2" />
              )}
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-800">
                <span className="text-2xl font-black text-white">C</span>
              </div>
              <span className="font-bold text-white">Chess.com</span>
              <span className="text-xs text-slate-400">chess.com</span>
            </button>
          </div>

          {/* Username inputs */}
          <div className="space-y-3">
            {platforms.has('lichess') && (
              <div className="space-y-1">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Lichess username
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                  <input
                    type="text"
                    value={lichessUser}
                    onChange={(e) => setLichessUser(e.target.value)}
                    placeholder="your-lichess-name"
                    className="w-full rounded-xl border border-kw-border bg-kw-surface py-3 pl-9 pr-4 text-sm text-white placeholder-slate-600 focus:border-kw-green/60 focus:outline-none focus:ring-1 focus:ring-kw-green/30"
                    autoComplete="off"
                    spellCheck={false}
                  />
                </div>
              </div>
            )}
            {platforms.has('chesscom') && (
              <div className="space-y-1">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Chess.com username
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                  <input
                    type="text"
                    value={chesscomUser}
                    onChange={(e) => setChesscomUser(e.target.value)}
                    placeholder="your-chess-com-name"
                    className="w-full rounded-xl border border-kw-border bg-kw-surface py-3 pl-9 pr-4 text-sm text-white placeholder-slate-600 focus:border-kw-green/60 focus:outline-none focus:ring-1 focus:ring-kw-green/30"
                    autoComplete="off"
                    spellCheck={false}
                  />
                </div>
              </div>
            )}
          </div>

          {formError && (
            <p className="rounded-xl border border-kw-red/30 bg-kw-red/10 px-3 py-2 text-sm text-red-300">
              {formError}
            </p>
          )}

          <button
            onClick={startImport}
            disabled={platforms.size === 0}
            className="btn-primary w-full"
          >
            Import my games <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* ── SYNCING ── */}
      {step === 'syncing' && (
        <div className="animate-slide-up w-full space-y-6 text-center">
          <div className="flex justify-center">
            {syncError ? (
              <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-kw-red/20">
                <RefreshCw className="h-10 w-10 text-kw-red" />
              </div>
            ) : (
              <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-kw-blue/20">
                <Loader2 className="h-10 w-10 text-kw-blue animate-spin" />
              </div>
            )}
          </div>

          {syncError ? (
            <div>
              <h2 className="text-xl font-extrabold text-white">Sync failed</h2>
              <p className="mt-2 text-sm text-kw-red">{syncError}</p>
              <button onClick={() => { setSyncError(''); setStep('platforms'); }} className="btn-secondary mt-4 w-full">
                Try again
              </button>
            </div>
          ) : (
            <>
              <div>
                <h2 className="text-xl font-extrabold text-white">
                  {syncStatus?.status === 'done' ? 'Analysis complete!' : 'Importing your games…'}
                </h2>
                <p className="mt-2 text-sm text-slate-400">{syncStatus?.message ?? 'Starting sync…'}</p>
              </div>

              {/* Progress bars */}
              <div className="space-y-3 text-left">
                {platforms.has('lichess') && (
                  <div>
                    <div className="mb-1 flex justify-between text-xs text-slate-400">
                      <span>Lichess</span>
                      <span>{syncStatus?.lichess_fetched ?? 0} games</span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-bar-fill bg-slate-300"
                        style={{ width: syncStatus?.lichess_fetched ? '100%' : '0%' }}
                      />
                    </div>
                  </div>
                )}
                {platforms.has('chesscom') && (
                  <div>
                    <div className="mb-1 flex justify-between text-xs text-slate-400">
                      <span>Chess.com</span>
                      <span>{syncStatus?.chesscom_fetched ?? 0} games</span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-bar-fill bg-green-400"
                        style={{ width: syncStatus?.chesscom_fetched ? '100%' : '0%' }}
                      />
                    </div>
                  </div>
                )}
                {(syncStatus?.total_games_to_analyze ?? 0) > 0 && (
                  <div>
                    <div className="mb-1 flex justify-between text-xs text-slate-400">
                      <span>Analysing positions</span>
                      <span>{syncStatus?.games_analyzed}/{syncStatus?.total_games_to_analyze}</span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-bar-fill bg-kw-purple"
                        style={{
                          width: `${Math.round(((syncStatus?.games_analyzed ?? 0) / (syncStatus?.total_games_to_analyze ?? 1)) * 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Live stats */}
              {totalFetched > 0 && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-2xl border border-kw-border bg-kw-surface p-3">
                    <div className="text-2xl font-extrabold text-white">{totalFetched}</div>
                    <div className="text-xs text-slate-400">games found</div>
                  </div>
                  <div className="rounded-2xl border border-kw-border bg-kw-surface p-3">
                    <div className="text-2xl font-extrabold text-white">{analyzedGames}</div>
                    <div className="text-xs text-slate-400">analysed</div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ── DONE ── */}
      {step === 'done' && (
        <div className="animate-bounce-in w-full space-y-6 text-center">
          <div className="flex justify-center">
            <div className="flex h-24 w-24 items-center justify-center rounded-3xl bg-kw-green/20 shadow-xl shadow-kw-green/10">
              <Trophy className="h-14 w-14 text-kw-yellow fill-kw-yellow/25" />
            </div>
          </div>

          <div>
            <h2 className="text-3xl font-extrabold text-white">You&apos;re all set!</h2>
            <p className="mt-2 text-slate-400">
              Your personalized training plan is ready.
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-2xl border border-kw-border bg-kw-surface p-3">
              <div className="text-2xl font-extrabold text-kw-green">{totalFetched}</div>
              <div className="text-xs text-slate-400">games imported</div>
            </div>
            <div className="rounded-2xl border border-kw-border bg-kw-surface p-3">
              <div className="text-2xl font-extrabold text-kw-blue">{analyzedGames}</div>
              <div className="text-xs text-slate-400">analysed</div>
            </div>
            <div className="rounded-2xl border border-kw-border bg-kw-surface p-3">
              <div className="text-2xl font-extrabold text-kw-purple">
                {platforms.has('lichess') && platforms.has('chesscom') ? 2 : 1}
              </div>
              <div className="text-xs text-slate-400">platform{platforms.size > 1 ? 's' : ''}</div>
            </div>
          </div>

          <div className="rounded-2xl border border-kw-green/30 bg-kw-green/10 p-4 text-left">
            <div className="flex items-center gap-2 text-sm font-bold text-kw-green">
              <CheckCircle2 className="h-4 w-4" />
              What&apos;s been set up for you
            </div>
            <ul className="mt-2 space-y-1 text-sm text-slate-300">
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-kw-green" />
                Daily Warp built from your weaknesses
              </li>
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-kw-green" />
                SRS drills tuned to your game themes
              </li>
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-kw-green" />
                Rating history from your real games
              </li>
            </ul>
          </div>

          <button onClick={goToDashboard} className="btn-primary w-full">
            Start training <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}

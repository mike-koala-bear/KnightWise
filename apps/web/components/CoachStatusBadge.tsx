'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import type { LLMHealth } from '@/lib/types';

/**
 * Tiny pill that surfaces whether coach notes are coming from the live
 * gpt-4o-mini model or the offline stub. We never call the OpenAI API from
 * here — `/v1/llm/health` only inspects local config — so this is cheap and
 * safe to render on every page.
 */
export function CoachStatusBadge() {
  const [data, setData] = useState<LLMHealth | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiGet<LLMHealth>('/v1/llm/health')
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error || !data) return null;

  const live = data.live;
  const color = live
    ? 'border-emerald-400/40 bg-emerald-500/10 text-emerald-200'
    : 'border-white/10 bg-white/5 text-slate-400';
  const label = live ? `AI coach live (${data.model})` : `AI coach: stub (${data.reason})`;

  return (
    <div
      data-testid="coach-status-badge"
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs ${color}`}
      title={label}
    >
      <span aria-hidden="true">{live ? '●' : '○'}</span>
      <span data-testid="coach-status-label">{label}</span>
    </div>
  );
}

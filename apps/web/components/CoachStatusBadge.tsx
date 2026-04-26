'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import type { LLMHealth } from '@/lib/types';

export function CoachStatusBadge() {
  const [data, setData] = useState<LLMHealth | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiGet<LLMHealth>('/v1/llm/health')
      .then((d) => { if (!cancelled) setData(d); })
      .catch(() => { /* silent */ });
    return () => { cancelled = true; };
  }, []);

  if (!data) return null;

  return (
    <div
      data-testid="coach-status-badge"
      className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${
        data.live
          ? 'border-kw-green/30 bg-kw-green/10 text-kw-green'
          : 'border-kw-border bg-kw-surface text-slate-500'
      }`}
      title={data.live ? `AI coach: ${data.model}` : `AI coach offline (${data.reason})`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${data.live ? 'bg-kw-green animate-pulse' : 'bg-slate-600'}`} />
      <span data-testid="coach-status-label">
        {data.live ? 'AI coach' : 'No AI coach'}
      </span>
    </div>
  );
}

'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { apiPost } from '@/lib/api';
import type { OnboardingState } from '@/lib/types';

type Props = { children: React.ReactNode };

export function OnboardingGuard({ children }: Props) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        // /onboarding/start is idempotent and returns completed_at without side-effects
        const state = await apiPost<OnboardingState>(
          '/v1/onboarding/start?user_id=1',
          {},
        );
        if (cancelled) return;
        if (!state.completed_at) {
          router.replace('/onboarding');
          return;
        }
      } catch {
        // API unreachable — unblock rather than loop forever
      }
      if (!cancelled) setReady(true);
    })();
    return () => { cancelled = true; };
  }, [router]);

  if (!ready) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-kw-green border-t-transparent" />
      </div>
    );
  }

  return <>{children}</>;
}

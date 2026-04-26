'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { apiPost } from '@/lib/api';
import type { OnboardingState } from '@/lib/types';

type Props = {
  children: React.ReactNode;
};

/**
 * Wraps protected pages. Redirects to /onboarding if the user hasn't
 * completed the skill test yet. Shows nothing while checking.
 */
export function OnboardingGuard({ children }: Props) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const state = await apiPost<OnboardingState>(
          '/v1/onboarding/start?user_id=1',
          {},
        );
        if (cancelled) return;
        if (!state.completed_at) {
          router.replace('/onboarding');
        } else {
          setReady(true);
        }
      } catch {
        // API unreachable — let the page render rather than blocking forever
        if (!cancelled) setReady(true);
      }
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

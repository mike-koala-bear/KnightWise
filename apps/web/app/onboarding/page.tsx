'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { OnboardingFlow } from '@/components/OnboardingFlow';
import { apiPost } from '@/lib/api';
import type { OnboardingState } from '@/lib/types';

export default function OnboardingPage() {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const state = await apiPost<OnboardingState>(
          '/v1/onboarding/start?user_id=1',
          {},
        );
        if (cancelled) return;
        if (state.completed_at) {
          router.replace('/app');
          return;
        }
      } catch { /* API down — proceed */ }
      if (!cancelled) setChecked(true);
    })();
    return () => { cancelled = true; };
  }, [router]);

  if (!checked) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-kw-green border-t-transparent" />
      </div>
    );
  }

  return <OnboardingFlow />;
}

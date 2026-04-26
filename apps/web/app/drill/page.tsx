import { DrillRunner } from '@/components/DrillRunner';
import { OnboardingGuard } from '@/components/OnboardingGuard';

type SearchParams = Promise<{ node?: string }>;

export default async function DrillPage({ searchParams }: { searchParams: SearchParams }) {
  const params = await searchParams;
  return (
    <OnboardingGuard>
      <DrillRunner {...(params.node ? { nodeSlug: params.node } : {})} />
    </OnboardingGuard>
  );
}

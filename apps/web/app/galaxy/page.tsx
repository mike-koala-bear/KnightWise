import { GalaxyPath } from '@/components/GalaxyPath';
import { OnboardingGuard } from '@/components/OnboardingGuard';

export default function GalaxyPage() {
  return (
    <OnboardingGuard>
      <div className="mx-auto max-w-5xl px-4 py-6">
        <div className="mb-6">
          <h1 className="text-2xl font-extrabold text-white">Galaxy Path</h1>
          <p className="mt-1 text-sm text-slate-400">
            A branching curriculum built around your weaknesses.
          </p>
        </div>
        <GalaxyPath userId={1} />
      </div>
    </OnboardingGuard>
  );
}

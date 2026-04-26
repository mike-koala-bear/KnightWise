import { DailyProgress } from '@/components/DailyProgress';
import { OnboardingGuard } from '@/components/OnboardingGuard';
import { RatingTracker } from '@/components/RatingTracker';
import { WarpView } from '@/components/WarpView';

export default function WarpPage() {
  return (
    <OnboardingGuard>
      <div className="mx-auto max-w-lg space-y-4 px-4 py-6">
        <div>
          <h1 className="text-2xl font-extrabold text-white">Daily Warp</h1>
          <p className="mt-1 text-sm text-slate-400">
            Your 15-minute personalized session, built from your last games.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <RatingTracker userId={1} days={7} />
          <DailyProgress userId={1} target={8} />
        </div>
        <WarpView userId={1} />
      </div>
    </OnboardingGuard>
  );
}

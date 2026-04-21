import { RatingTracker } from '@/components/RatingTracker';
import { WarpView } from '@/components/WarpView';

export default function WarpPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-8 px-6 py-10">
      <header className="text-center">
        <h1 className="text-3xl font-bold tracking-tight">Daily Warp</h1>
        <p className="mt-1 text-sm text-slate-400">
          Your 15-minute personalized training session, composed from your last games.
        </p>
      </header>
      <RatingTracker userId={1} days={7} />
      <WarpView userId={1} />
    </main>
  );
}

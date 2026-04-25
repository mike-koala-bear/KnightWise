import { OnboardingRunner } from '@/components/OnboardingRunner';

export default function OnboardingPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center gap-6 px-6 py-10">
      <header className="text-center">
        <h1 className="text-3xl font-bold tracking-tight">Skill test</h1>
        <p className="mt-1 text-sm text-slate-400">
          ~10 minutes. Sets your starting Elo so every drill afterwards is at the
          right difficulty.
        </p>
      </header>
      <OnboardingRunner userId={1} />
    </main>
  );
}

import { GalaxyPath } from '@/components/GalaxyPath';

export default function GalaxyPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-6 px-6 py-10">
      <header className="text-center">
        <h1 className="text-3xl font-bold tracking-tight">Galaxy Path</h1>
        <p className="mt-1 text-sm text-slate-400">
          A 2D branching curriculum. Today&apos;s recommended branch is
          highlighted based on your #1 weakness.
        </p>
      </header>
      <GalaxyPath userId={1} />
    </main>
  );
}

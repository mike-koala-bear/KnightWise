import { DrillRunner } from '@/components/DrillRunner';

type SearchParams = Promise<{ node?: string }>;

export default async function DrillPage({ searchParams }: { searchParams: SearchParams }) {
  const params = await searchParams;
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center gap-6 px-6 py-10">
      <header className="text-center">
        <h1 className="text-3xl font-bold tracking-tight">Drill</h1>
        <p className="mt-1 text-sm text-slate-400">
          Solve the position. Correct moves update your SRS schedule.
        </p>
      </header>
      <DrillRunner {...(params.node ? { nodeSlug: params.node } : {})} />
    </main>
  );
}

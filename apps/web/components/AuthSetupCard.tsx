import type { Route } from 'next';
import Link from 'next/link';

export function AuthSetupCard({ mode }: { mode: 'sign-in' | 'sign-up' }) {
  const title = mode === 'sign-in' ? 'Sign in' : 'Create your account';
  const alternate =
    mode === 'sign-in'
      ? { href: '/sign-up', label: 'Need an account? Sign up' }
      : { href: '/sign-in', label: 'Already have an account? Sign in' };

  return (
    <div className="mx-auto w-full max-w-md rounded-2xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/30">
      <p className="text-xs font-semibold uppercase tracking-[0.25em] text-indigo-300">
        KnightWise auth
      </p>
      <h1 className="mt-3 text-2xl font-bold">{title}</h1>
      <p className="mt-3 text-sm leading-6 text-slate-300">
        Clerk is wired up, but this local app is still using placeholder keys.
        Add your real Clerk keys to <code className="text-slate-100">apps/web/.env.local</code>,
        then restart the dev server to enable the full login and signup forms.
      </p>
      <div className="mt-5 rounded-lg border border-white/10 bg-slate-950/50 p-4 text-xs text-slate-300">
        <div>NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...</div>
        <div>CLERK_SECRET_KEY=sk_test_...</div>
      </div>
      <div className="mt-6 flex items-center justify-between gap-3">
        <Link
          href="/"
          className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-200 transition hover:bg-white/10"
        >
          Back home
        </Link>
        <Link href={alternate.href as Route} className="text-sm font-medium text-indigo-300 hover:text-indigo-200">
          {alternate.label}
        </Link>
      </div>
    </div>
  );
}

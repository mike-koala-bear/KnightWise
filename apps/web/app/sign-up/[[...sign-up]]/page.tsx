import { SignUp } from '@clerk/nextjs';
import type { Route } from 'next';
import Link from 'next/link';

import { clerkIsConfigured } from '@/lib/clerk';

export default function SignUpPage() {
  if (clerkIsConfigured()) {
    return (
      <main className="flex min-h-[calc(100vh-5rem)] items-center justify-center px-6 py-12">
        <SignUp
          path="/sign-up"
          routing="path"
          signInUrl="/sign-in"
          fallbackRedirectUrl="/onboarding"
        />
      </main>
    );
  }

  return (
    <main className="flex min-h-[calc(100vh-5rem)] items-center justify-center px-6 py-12">
      <div className="mx-auto w-full max-w-sm space-y-6 text-center">
        <div className="flex justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-kw-green/20 text-4xl">
            ♞
          </div>
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-white">Welcome to KnightWise</h1>
          <p className="mt-2 text-sm text-slate-400">
            No account needed right now — jump straight into the skill test to calibrate your Elo.
          </p>
        </div>
        <Link href={'/onboarding' as Route} className="btn-primary block w-full">
          Start skill test →
        </Link>
        <p className="text-xs text-slate-600">
          Add Clerk keys to <code className="text-slate-400">apps/web/.env.local</code> to enable real accounts.
        </p>
      </div>
    </main>
  );
}

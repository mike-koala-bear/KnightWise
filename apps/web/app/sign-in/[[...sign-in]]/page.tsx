import { SignIn } from '@clerk/nextjs';
import type { Route } from 'next';
import Link from 'next/link';

import { clerkIsConfigured } from '@/lib/clerk';

export default function SignInPage() {
  if (clerkIsConfigured()) {
    return (
      <main className="flex min-h-[calc(100vh-5rem)] items-center justify-center px-6 py-12">
        <SignIn
          path="/sign-in"
          routing="path"
          signUpUrl="/sign-up"
          fallbackRedirectUrl="/app"
        />
      </main>
    );
  }

  return (
    <main className="flex min-h-[calc(100vh-5rem)] items-center justify-center px-6 py-12">
      <div className="mx-auto w-full max-w-sm space-y-6 text-center">
        <div className="flex justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-kw-blue/20 text-4xl">
            ♞
          </div>
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-white">Sign in</h1>
          <p className="mt-2 text-sm text-slate-400">
            Add your Clerk keys to enable real authentication, or continue as the default user.
          </p>
        </div>
        <Link href={'/app' as Route} className="btn-primary block w-full">
          Continue →
        </Link>
        <p className="text-xs text-slate-600">
          Add Clerk keys to <code className="text-slate-400">apps/web/.env.local</code> for full auth.
        </p>
      </div>
    </main>
  );
}

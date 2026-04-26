import { SignedIn, SignedOut, UserButton } from '@clerk/nextjs';
import type { Route } from 'next';
import Link from 'next/link';

import { clerkIsConfigured } from '@/lib/clerk';

export function AuthNav() {
  if (!clerkIsConfigured()) {
    return (
      <div className="flex items-center gap-2">
        <Link
          href={'/sign-in' as Route}
          className="rounded-xl border border-kw-border px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-kw-surface transition-colors"
        >
          Login
        </Link>
        <Link
          href={'/sign-up' as Route}
          className="rounded-xl bg-kw-green px-3 py-1.5 text-xs font-bold text-white hover:brightness-110 transition-filter"
        >
          Sign up
        </Link>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <SignedOut>
        <Link
          href={'/sign-in' as Route}
          className="rounded-xl border border-kw-border px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-kw-surface transition-colors"
        >
          Login
        </Link>
        <Link
          href={'/sign-up' as Route}
          className="rounded-xl bg-kw-green px-3 py-1.5 text-xs font-bold text-white hover:brightness-110 transition-filter"
        >
          Sign up
        </Link>
      </SignedOut>
      <SignedIn>
        <UserButton appearance={{ elements: { avatarBox: 'h-8 w-8' } }} />
      </SignedIn>
    </div>
  );
}

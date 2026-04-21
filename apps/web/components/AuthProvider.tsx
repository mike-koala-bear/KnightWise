import { ClerkProvider } from '@clerk/nextjs';
import type { ReactNode } from 'react';

/**
 * Wraps the app in Clerk only when a publishable key is set. Keeps local dev
 * and CI green without real keys; once you add pk_test_... to .env.local the
 * app transparently switches to full Clerk auth.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const pk = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const enabled = pk && pk !== 'pk_test_placeholder' && pk.startsWith('pk_');

  if (!enabled) return <>{children}</>;
  return <ClerkProvider>{children}</ClerkProvider>;
}

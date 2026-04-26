import { ClerkProvider } from '@clerk/nextjs';
import type { ReactNode } from 'react';

import { clerkIsConfigured } from '@/lib/clerk';

/**
 * Wraps the app in Clerk only when a publishable key is set. Keeps local dev
 * and CI green without real keys; once you add pk_test_... to .env.local the
 * app transparently switches to full Clerk auth.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  if (!clerkIsConfigured()) return <>{children}</>;

  return <ClerkProvider>{children}</ClerkProvider>;
}

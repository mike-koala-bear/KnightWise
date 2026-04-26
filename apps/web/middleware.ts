import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { clerkIsConfigured } from './lib/clerk';

const isAuthRoute = createRouteMatcher(['/sign-in(.*)', '/sign-up(.*)']);
const isProtectedRoute = createRouteMatcher([
  '/app(.*)',
  '/drill(.*)',
  '/galaxy(.*)',
  '/onboarding(.*)',
  '/warp(.*)',
]);

// In placeholder mode (no Clerk), all protected routes are accessible
// directly — the OnboardingGuard component handles post-signup redirection.
function placeholderAuthMiddleware(_request: NextRequest) {
  return NextResponse.next();
}

const clerkAuthMiddleware = clerkMiddleware(async (auth, request) => {
  const { userId } = await auth();

  if (!userId && isProtectedRoute(request)) {
    const signInUrl = new URL('/sign-in', request.url);
    signInUrl.searchParams.set('redirect_url', request.nextUrl.pathname);
    return NextResponse.redirect(signInUrl);
  }

  if (userId && (request.nextUrl.pathname === '/' || isAuthRoute(request))) {
    return NextResponse.redirect(new URL('/app', request.url));
  }

  return NextResponse.next();
});

export default function middleware(request: NextRequest, event: Parameters<typeof clerkAuthMiddleware>[1]) {
  if (!clerkIsConfigured()) {
    return placeholderAuthMiddleware(request);
  }

  return clerkAuthMiddleware(request, event);
}

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ico|woff2?|ttf|map)).*)',
    '/(api|trpc)(.*)',
  ],
};

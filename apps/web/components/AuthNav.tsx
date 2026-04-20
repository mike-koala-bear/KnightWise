import { SignInButton, SignedIn, SignedOut, UserButton } from '@clerk/nextjs';

export function AuthNav() {
  const pk = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const enabled = pk && pk !== 'pk_test_placeholder' && pk.startsWith('pk_');
  if (!enabled) return null;

  return (
    <div className="flex items-center gap-2 text-xs">
      <SignedOut>
        <SignInButton mode="modal">
          <button
            type="button"
            className="rounded border border-white/20 px-3 py-1.5 hover:bg-white/10"
          >
            Sign in
          </button>
        </SignInButton>
      </SignedOut>
      <SignedIn>
        <UserButton appearance={{ elements: { avatarBox: 'h-7 w-7' } }} />
      </SignedIn>
    </div>
  );
}

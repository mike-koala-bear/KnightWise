export function clerkIsConfigured() {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const secretKey = process.env.CLERK_SECRET_KEY;

  return Boolean(
    publishableKey &&
      secretKey &&
      publishableKey !== 'pk_test_placeholder' &&
      secretKey !== 'sk_test_placeholder' &&
      publishableKey.startsWith('pk_') &&
      secretKey.startsWith('sk_'),
  );
}

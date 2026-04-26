import { Dashboard } from '@/components/Dashboard';
import { OnboardingGuard } from '@/components/OnboardingGuard';

export default function AppPage() {
  return (
    <OnboardingGuard>
      <Dashboard />
    </OnboardingGuard>
  );
}

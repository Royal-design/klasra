import { LandingNavbar } from "@/components/landing/navbar";
import { LandingHero } from "@/components/landing/hero";
import { BentoFeatures } from "@/components/landing/bento-features";
import { RoleShowcase } from "@/components/landing/role-showcase";
import { OnboardingAndSecurity } from "@/components/landing/onboarding-and-security";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <LandingNavbar />
      <main className="flex-1">
        <LandingHero />
        <BentoFeatures />
        <RoleShowcase />
        <OnboardingAndSecurity />
      </main>
    </div>
  );
}

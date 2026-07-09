import HeroSection from "@/features/landing/components/HeroSection";
import ProductPreview from "@/features/landing/components/ProductPreview";
import FeaturesGrid from "@/features/landing/components/FeaturesGrid";
import WhyLifePilot from "@/features/landing/components/WhyLifePilot";
import ArchitectureFlow from "@/features/landing/components/ArchitectureFlow";
import TechStackSection from "@/features/landing/components/TechStackSection";
import RoadmapTimeline from "@/features/landing/components/RoadmapTimeline";
import LandingFooter from "@/features/landing/components/LandingFooter";

import { PageWrapper } from "@/layouts/PageWrapper";
import Navbar from "@/layouts/Navbar";

export default function Home() {
  return (
    <PageWrapper className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 selection:bg-indigo-500 selection:text-white font-sans overflow-x-hidden">
      <Navbar />

      {/* Main Sections Stack */}
      <main>
        <HeroSection />
        <ProductPreview />
        <FeaturesGrid />
        <WhyLifePilot />
        <ArchitectureFlow />
        <TechStackSection />
        <RoadmapTimeline />
      </main>

      <LandingFooter />
    </PageWrapper>
  );
}

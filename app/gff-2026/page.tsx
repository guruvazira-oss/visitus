import type { Metadata } from "next";
import GffNavbar from "@/components/GffNavbar";
import GffHero from "@/components/GffHero";
import EventStrip from "@/components/EventStrip";
import IndiaVoiceSection from "@/components/IndiaVoiceSection";
import ConversationDemo from "@/components/ConversationDemo";
import BfsiSolutions from "@/components/BfsiSolutions";
import EnterpriseArchitecture from "@/components/EnterpriseArchitecture";
import PlatformPillars from "@/components/PlatformPillars";
import GffExperience from "@/components/GffExperience";
import TeamSection from "@/components/TeamSection";
import EventSection from "@/components/EventSection";
import FinalCTA from "@/components/FinalCTA";
import GffFooter from "@/components/GffFooter";

export const metadata: Metadata = {
  title: "Voice India at Global Fintech Fest 2026 | AI-Powered Conversations",
  description:
    "Meet Voice India at Global Fintech Fest 2026 and experience enterprise AI voice agents built for India's conversations, workflows and customer outcomes.",
  openGraph: {
    title: "Voice India at Global Fintech Fest 2026 | AI-Powered Conversations",
    description:
      "Meet Voice India at Global Fintech Fest 2026 and experience enterprise AI voice agents built for India's conversations, workflows and customer outcomes.",
    type: "website",
    locale: "en_IN",
  },
};

export default function GFF2026Page() {
  return (
    <main>
      <GffNavbar />

      {/* ACT 01 — THE EVENT */}
      <GffHero />

      {/* Event strip */}
      <EventStrip />

      {/* ACT 02 + 03 — THE PROBLEM + THE INDIA INSIGHT */}
      <IndiaVoiceSection />

      {/* ACT 05 — THE CONVERSATION */}
      <ConversationDemo />

      {/* ACT 06 — THE BFSI WORKFLOWS */}
      <BfsiSolutions />

      {/* ACT 07 — THE ENTERPRISE PLATFORM */}
      <EnterpriseArchitecture />

      {/* ACT 08 — TRUST / SECURITY / SCALE + ACT 16 WHY VOICE INDIA */}
      <PlatformPillars />

      {/* ACT 09 — EXPERIENCE IT AT GFF */}
      <GffExperience />

      {/* ACT 10 — MEET VOICE INDIA */}
      <TeamSection />

      {/* Event details */}
      <EventSection />

      {/* ACT 11 — FINAL CTA */}
      <FinalCTA />

      <GffFooter />
    </main>
  );
}

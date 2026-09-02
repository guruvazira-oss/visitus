"use client";

import { motion } from "framer-motion";
import Image from "next/image";

export default function GffHero() {
  return (
    <section
      className="relative min-h-screen flex flex-col overflow-hidden"
      aria-label="Hero — Voice India at GFF 2026"
    >
      {/* Background image */}
      <div className="absolute inset-0 z-0">
        <Image
          src="/assets/voice-india-gff-background.svg"
          alt="Voice India wave background — deep navy waves on soft white with sunrise orange and India green accents"
          fill
          priority
          style={{ objectFit: "cover", objectPosition: "center bottom" }}
        />
        {/* Subtle overlay to enhance text legibility at top */}
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(180deg, rgba(7,24,73,0.25) 0%, rgba(7,24,73,0.05) 40%, transparent 70%)",
          }}
        />
      </div>

      {/* Wave animation overlay */}
      <div className="absolute bottom-0 left-0 right-0 h-48 z-0 pointer-events-none">
        <motion.div
          animate={{ y: [0, -6, 0] }}
          transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(0deg, rgba(7,24,73,0.08) 0%, transparent 100%)",
          }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col flex-1 max-w-7xl mx-auto px-6 lg:px-8 pt-32 pb-20">
        {/* Eyebrow */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="flex items-center gap-3 mb-8"
        >
          <span
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold tracking-widest uppercase"
            style={{
              background: "rgba(255,104,26,0.15)",
              border: "1px solid rgba(255,104,26,0.4)",
              color: "#FF681A",
              backdropFilter: "blur(8px)",
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: "#FF681A" }}
            />
            Global Fintech Fest 2026
          </span>
        </motion.div>

        {/* Main headline */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.35 }}
          className="text-5xl sm:text-6xl lg:text-7xl xl:text-8xl font-bold leading-none tracking-tight max-w-4xl"
        >
          <span
            className="block mb-2"
            style={{ color: "#FFFFFF", textShadow: "0 2px 20px rgba(7,24,73,0.3)" }}
          >
            AI-Powered
          </span>
          <span
            className="block mb-2"
            style={{ color: "#FFFFFF", textShadow: "0 2px 20px rgba(7,24,73,0.3)" }}
          >
            Conversations.
          </span>
          <span style={{ color: "#FF681A", textShadow: "0 2px 30px rgba(255,104,26,0.4)" }}>
            Stronger Outcomes.
          </span>
        </motion.h1>

        {/* Supporting copy */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.55 }}
          className="mt-8 text-lg sm:text-xl max-w-2xl leading-relaxed"
          style={{ color: "rgba(255,255,255,0.88)", textShadow: "0 1px 8px rgba(7,24,73,0.2)" }}
        >
          Voice India is building the voice intelligence layer for India&apos;s
          enterprises — helping businesses automate conversations, accelerate
          workflows and create stronger customer outcomes.
        </motion.p>

        {/* Event details */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="flex items-center gap-4 mt-8 mb-10"
        >
          <div
            className="flex items-center gap-3 px-4 py-2.5 rounded-xl"
            style={{
              background: "rgba(255,255,255,0.12)",
              backdropFilter: "blur(12px)",
              border: "1px solid rgba(255,255,255,0.2)",
            }}
          >
            <CalendarIcon />
            <span
              className="text-sm font-medium"
              style={{ color: "rgba(255,255,255,0.95)" }}
            >
              08–11 September 2026
            </span>
          </div>
          <div
            className="flex items-center gap-3 px-4 py-2.5 rounded-xl"
            style={{
              background: "rgba(255,255,255,0.12)",
              backdropFilter: "blur(12px)",
              border: "1px solid rgba(255,255,255,0.2)",
            }}
          >
            <LocationIcon />
            <span
              className="text-sm font-medium"
              style={{ color: "rgba(255,255,255,0.95)" }}
            >
              Jio World Centre, BKC, Mumbai
            </span>
          </div>
        </motion.div>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.85 }}
          className="flex flex-wrap gap-4"
        >
          <a
            href="#book-meeting"
            className="inline-flex items-center gap-2.5 px-8 py-4 rounded-full text-sm font-bold tracking-wide text-white transition-all duration-200 hover:scale-105 focus-visible:outline-2 focus-visible:outline-white"
            style={{
              background: "linear-gradient(135deg, #FF681A 0%, #E85500 100%)",
              boxShadow: "0 8px 32px rgba(255,104,26,0.4)",
            }}
          >
            <span>MEET VOICE INDIA</span>
            <ArrowRight />
          </a>
          <a
            href="#conversation-demo"
            className="inline-flex items-center gap-2.5 px-8 py-4 rounded-full text-sm font-bold tracking-wide transition-all duration-200 hover:scale-105 focus-visible:outline-2 focus-visible:outline-white"
            style={{
              background: "rgba(255,255,255,0.12)",
              backdropFilter: "blur(12px)",
              border: "1px solid rgba(255,255,255,0.35)",
              color: "white",
            }}
          >
            <MicIcon />
            <span>TALK TO OUR AI</span>
          </a>
        </motion.div>

        {/* Floating scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5, duration: 0.6 }}
          className="absolute bottom-10 left-1/2 -translate-x-1/2"
        >
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
          >
            <ChevronDown />
          </motion.div>
        </motion.div>
      </div>

      {/* Animated wave particles */}
      <HeroParticles />
    </section>
  );
}

function HeroParticles() {
  return (
    <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
      {[...Array(12)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full"
          style={{
            width: Math.random() * 4 + 2,
            height: Math.random() * 4 + 2,
            left: `${10 + i * 8}%`,
            top: `${20 + (i % 5) * 12}%`,
            background:
              i % 3 === 0
                ? "rgba(255,104,26,0.6)"
                : i % 3 === 1
                ? "rgba(255,255,255,0.5)"
                : "rgba(59,158,255,0.5)",
          }}
          animate={{
            y: [0, -15, 0],
            opacity: [0.4, 0.8, 0.4],
          }}
          transition={{
            duration: 4 + (i % 4),
            repeat: Infinity,
            delay: i * 0.4,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}

function CalendarIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <rect x="1" y="2.5" width="14" height="12" rx="2" stroke="rgba(255,255,255,0.7)" strokeWidth="1.2" fill="none" />
      <path d="M5 1v3M11 1v3M1 6h14" stroke="rgba(255,255,255,0.7)" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

function LocationIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M8 1.5C5.5 1.5 3.5 3.5 3.5 6C3.5 9.5 8 14.5 8 14.5C8 14.5 12.5 9.5 12.5 6C12.5 3.5 10.5 1.5 8 1.5Z" stroke="rgba(255,255,255,0.7)" strokeWidth="1.2" fill="none" />
      <circle cx="8" cy="6" r="1.5" stroke="rgba(255,255,255,0.7)" strokeWidth="1.2" fill="none" />
    </svg>
  );
}

function ArrowRight() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function MicIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <rect x="5" y="1" width="6" height="8" rx="3" stroke="currentColor" strokeWidth="1.3" fill="none" />
      <path d="M2.5 7.5C2.5 10.5 5 13 8 13C11 13 13.5 10.5 13.5 7.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" fill="none" />
      <line x1="8" y1="13" x2="8" y2="15" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <line x1="5.5" y1="15" x2="10.5" y2="15" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

function ChevronDown() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M6 9l6 6 6-6" stroke="rgba(255,255,255,0.6)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

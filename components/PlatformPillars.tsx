"use client";

import React, { useRef } from "react";
import { motion, useInView } from "framer-motion";

const pillars = [
  {
    id: "ai-first",
    label: "AI-FIRST",
    body: "Intelligent conversations that adapt and resolve — going beyond scripted flows to genuinely understand intent.",
    icon: "BrainIcon",
    accent: "#3B9EFF",
  },
  {
    id: "compliant",
    label: "COMPLIANT",
    body: "Designed for enterprise and regulated environments, with attention to the requirements of India's financial sector.",
    icon: "ShieldIcon",
    accent: "#FF681A",
  },
  {
    id: "secure",
    label: "SECURE",
    body: "Your data. Your cloud. Your control. Voice India is built for enterprise data governance requirements.",
    icon: "LockIcon",
    accent: "#16A34A",
  },
  {
    id: "scalable",
    label: "SCALABLE",
    body: "Built to support enterprise-scale interactions — from pilot deployments to full-scale operations.",
    icon: "ScaleIcon",
    accent: "#1E6FD9",
  },
];

export default function PlatformPillars() {
  const ref = useRef<HTMLElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      className="relative py-24 lg:py-36 overflow-hidden"
      style={{ background: "#071849" }}
      aria-label="Platform pillars"
    >
      {/* Background SVG wave decoration */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <svg
          className="absolute bottom-0 left-0 right-0 w-full"
          viewBox="0 0 1440 200"
          preserveAspectRatio="none"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M0 100 Q360 60 720 80 Q1080 100 1440 60 L1440 200 L0 200 Z"
            fill="rgba(16,42,92,0.4)"
          />
          <path
            d="M0 140 Q360 110 720 125 Q1080 140 1440 110 L1440 200 L0 200 Z"
            fill="rgba(16,42,92,0.3)"
          />
        </svg>

        {/* Dot grid pattern */}
        <svg
          className="absolute inset-0 w-full h-full opacity-10"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <defs>
            <pattern
              id="dots"
              x="0"
              y="0"
              width="40"
              height="40"
              patternUnits="userSpaceOnUse"
            >
              <circle cx="2" cy="2" r="1.5" fill="#3B9EFF" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#dots)" />
        </svg>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5 }}
            className="inline-block text-xs font-semibold tracking-widest uppercase mb-4"
            style={{ color: "#FF681A" }}
          >
            Act 08 — Trust · Security · Scale
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight"
            style={{ color: "white" }}
          >
            Built for enterprise.
            <br />
            <span style={{ color: "#FF681A" }}>Built for India.</span>
          </motion.h2>
        </div>

        {/* Pillars */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {pillars.map((pillar, i) => (
            <motion.div
              key={pillar.id}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: 0.15 + i * 0.1 }}
              className="relative p-7 rounded-2xl group transition-all duration-300 hover:-translate-y-2"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              {/* Hover glow */}
              <div
                className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
                style={{
                  border: `1px solid ${pillar.accent}50`,
                  boxShadow: `0 0 40px ${pillar.accent}15`,
                }}
              />

              {/* Icon */}
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-6"
                style={{
                  background: `${pillar.accent}15`,
                  border: `1px solid ${pillar.accent}30`,
                }}
              >
                <PillarIcon name={pillar.icon} color={pillar.accent} />
              </div>

              {/* Label */}
              <div
                className="text-xs font-bold tracking-widest uppercase mb-3"
                style={{ color: pillar.accent }}
              >
                {pillar.label}
              </div>

              {/* Body */}
              <p
                className="text-sm leading-relaxed"
                style={{ color: "rgba(255,255,255,0.6)" }}
              >
                {pillar.body}
              </p>

              {/* Bottom accent line */}
              <div
                className="absolute bottom-0 left-0 right-0 h-0.5 rounded-b-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                style={{ background: `linear-gradient(90deg, transparent, ${pillar.accent}, transparent)` }}
              />
            </motion.div>
          ))}
        </div>

        {/* Why Voice India */}
        <div className="mt-20 pt-16 border-t" style={{ borderColor: "rgba(255,255,255,0.08)" }}>
          <motion.h3
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="text-3xl sm:text-4xl font-bold text-center mb-12"
            style={{ color: "white" }}
          >
            The next generation of customer interaction
            <br />
            <span style={{ color: "#FF681A" }}>is conversational.</span>
          </motion.h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                title: "India-first voice intelligence",
                sub: "Built around how India's customers actually communicate.",
                color: "#FF681A",
              },
              {
                title: "Natural multilingual conversations",
                sub: "Handles the full spectrum of Indian languages and code-switching.",
                color: "#3B9EFF",
              },
              {
                title: "Enterprise workflow integration",
                sub: "Connects voice intelligence directly to business systems and actions.",
                color: "#16A34A",
              },
              {
                title: "Human + AI orchestration",
                sub: "Intelligent handoffs between AI and human agents at the right moment.",
                color: "#FF681A",
              },
            ].map((item, i) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.5, delay: 0.55 + i * 0.08 }}
                className="flex flex-col"
              >
                <div
                  className="w-8 h-1 rounded-full mb-4"
                  style={{ background: item.color }}
                />
                <h4
                  className="text-base font-bold mb-2"
                  style={{ color: "white" }}
                >
                  {item.title}
                </h4>
                <p className="text-sm" style={{ color: "rgba(255,255,255,0.55)" }}>
                  {item.sub}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function PillarIcon({ name, color }: { name: string; color: string }) {
  const icons: Record<string, React.ReactElement> = {
    BrainIcon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
        <path d="M11 3C8 3 6 5 6 7.5C4.5 7.5 3 8.8 3 10.5C3 12.2 4.2 13.5 6 13.5V17C6 18.1 6.9 19 8 19h6c1.1 0 2-.9 2-2v-3.5c1.8 0 3-1.3 3-3C19 8.8 17.5 7.5 16 7.5C16 5 14 3 11 3Z" stroke={color} strokeWidth="1.3" fill="none" />
        <path d="M11 3v16M8 11h6M8 14h6" stroke={color} strokeWidth="1.1" strokeLinecap="round" opacity="0.5" />
      </svg>
    ),
    ShieldIcon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
        <path d="M11 2L4 5v6c0 5 3.5 9 7 9s7-4 7-9V5L11 2Z" stroke={color} strokeWidth="1.3" fill="none" />
        <path d="M8 11l2 2 4-4" stroke={color} strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    LockIcon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
        <rect x="4" y="10" width="14" height="10" rx="2" stroke={color} strokeWidth="1.3" fill="none" />
        <path d="M7 10V7a4 4 0 018 0v3" stroke={color} strokeWidth="1.3" fill="none" />
        <circle cx="11" cy="15" r="1.5" fill={color} opacity="0.6" />
      </svg>
    ),
    ScaleIcon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
        <path d="M4 16l5-8 3 4 3-6 3 10" stroke={color} strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        <path d="M2 16h18" stroke={color} strokeWidth="1.3" strokeLinecap="round" />
      </svg>
    ),
  };
  return icons[name] ?? null;
}

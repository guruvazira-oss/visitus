"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";

// Replace with actual team data when available
const teamConfig = [
  {
    name: "[NAME]",
    role: "[Co-Founder & CEO]",
    bio: "Building India's voice intelligence infrastructure.",
    initials: "VI",
    bg: "#071849",
  },
  {
    name: "[NAME]",
    role: "[Co-Founder & CTO]",
    bio: "Architecting enterprise-grade AI systems.",
    initials: "VI",
    bg: "#102A5C",
  },
  {
    name: "[NAME]",
    role: "[Head of Product]",
    bio: "Designing conversations that create enterprise value.",
    initials: "VI",
    bg: "#071849",
  },
];

export default function TeamSection() {
  const ref = useRef<HTMLElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      className="relative py-24 lg:py-32"
      style={{ background: "#F3F6FA" }}
      aria-label="Team section"
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <div className="max-w-2xl mb-16">
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5 }}
            className="inline-block text-xs font-semibold tracking-widest uppercase mb-4"
            style={{ color: "#FF681A" }}
          >
            Act 10 — Meet Voice India
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl font-bold leading-tight"
            style={{ color: "#071849" }}
          >
            The people building India&apos;s
            <br />
            <span style={{ color: "#FF681A" }}>voice intelligence layer.</span>
          </motion.h2>
        </div>

        {/* Team cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {teamConfig.map((member, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 24 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: 0.15 + i * 0.1 }}
              className="p-7 rounded-2xl group transition-all duration-300 hover:-translate-y-1"
              style={{
                background: "white",
                border: "1px solid rgba(7,24,73,0.08)",
                boxShadow: "0 2px 16px rgba(7,24,73,0.05)",
              }}
            >
              {/* Avatar */}
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5 text-white font-bold text-lg"
                style={{ background: member.bg }}
              >
                {member.initials}
              </div>

              {/* Content */}
              <h3
                className="text-lg font-bold mb-1"
                style={{ color: "#071849" }}
              >
                {member.name}
              </h3>
              <div
                className="text-xs font-semibold tracking-wider uppercase mb-3"
                style={{ color: "#FF681A" }}
              >
                {member.role}
              </div>
              <p className="text-sm leading-relaxed" style={{ color: "#6B7BA8" }}>
                {member.bio}
              </p>
            </motion.div>
          ))}
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="text-center text-xs mt-8"
          style={{ color: "#9BA8C8" }}
        >
          Team profiles updated closer to GFF 2026.
        </motion.p>
      </div>
    </section>
  );
}

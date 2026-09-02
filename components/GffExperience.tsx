"use client";

import React, { useRef } from "react";
import { motion, useInView } from "framer-motion";

const experiences = [
  {
    num: "01",
    title: "TALK TO OUR AI",
    body: "Experience a real voice conversation powered by Voice India's enterprise AI — directly at our booth.",
    icon: "MicIcon",
    color: "#FF681A",
  },
  {
    num: "02",
    title: "SEE THE WORKFLOW",
    body: "Watch as a natural conversation becomes structured enterprise action — in real time, in your industry context.",
    icon: "FlowIcon",
    color: "#1E6FD9",
  },
  {
    num: "03",
    title: "MEET THE TEAM",
    body: "Discuss your specific business use case with the Voice India team and explore how voice intelligence applies to your organisation.",
    icon: "TeamIcon",
    color: "#16A34A",
  },
];

export default function GffExperience() {
  const ref = useRef<HTMLElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      id="gff-experience"
      className="relative py-24 lg:py-36 overflow-hidden"
      style={{ background: "white" }}
      aria-label="GFF 2026 experience"
    >
      {/* Decorative background wave */}
      <div
        className="absolute bottom-0 left-0 right-0 h-32 pointer-events-none"
        style={{
          background: "linear-gradient(0deg, #F3F6FA 0%, transparent 100%)",
        }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5 }}
            className="inline-block text-xs font-semibold tracking-widest uppercase mb-4"
            style={{ color: "#FF681A" }}
          >
            Act 09 — Experience It at GFF
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight"
            style={{ color: "#071849" }}
          >
            Experience Voice India
            <br />
            <span style={{ color: "#FF681A" }}>at GFF 2026.</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-6 text-xl"
            style={{ color: "#4B5880" }}
          >
            Don&apos;t just hear about Voice AI.{" "}
            <span style={{ color: "#071849", fontWeight: 600 }}>Talk to it.</span>
          </motion.p>
        </div>

        {/* Experience cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-14">
          {experiences.map((exp, i) => (
            <motion.div
              key={exp.num}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: 0.2 + i * 0.1 }}
              className="relative p-8 rounded-2xl group transition-all duration-300 hover:-translate-y-2"
              style={{
                background: "#F3F6FA",
                border: "1px solid rgba(7,24,73,0.08)",
              }}
            >
              {/* Hover effect */}
              <div
                className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
                style={{
                  border: `1.5px solid ${exp.color}40`,
                  boxShadow: `0 12px 40px ${exp.color}10`,
                }}
              />

              {/* Number */}
              <div
                className="text-5xl font-black mb-5 leading-none"
                style={{
                  color: `${exp.color}15`,
                  fontVariantNumeric: "tabular-nums",
                }}
                aria-hidden="true"
              >
                {exp.num}
              </div>

              {/* Icon */}
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-5"
                style={{
                  background: `${exp.color}12`,
                  border: `1px solid ${exp.color}30`,
                }}
              >
                <ExpIcon name={exp.icon} color={exp.color} />
              </div>

              {/* Content */}
              <h3
                className="text-sm font-bold tracking-widest uppercase mb-3"
                style={{ color: exp.color }}
              >
                {exp.title}
              </h3>
              <p className="text-base leading-relaxed" style={{ color: "#4B5880" }}>
                {exp.body}
              </p>
            </motion.div>
          ))}
        </div>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="flex flex-wrap gap-4 justify-center"
        >
          <a
            href="#book-meeting"
            className="inline-flex items-center gap-2.5 px-8 py-4 rounded-full text-sm font-bold tracking-wide text-white transition-all duration-200 hover:scale-105 focus-visible:outline-2 focus-visible:outline-orange-500"
            style={{
              background: "linear-gradient(135deg, #FF681A 0%, #E85500 100%)",
              boxShadow: "0 8px 32px rgba(255,104,26,0.3)",
            }}
          >
            BOOK A MEETING
          </a>
          <a
            href="#conversation-demo"
            className="inline-flex items-center gap-2.5 px-8 py-4 rounded-full text-sm font-bold tracking-wide transition-all duration-200 hover:scale-105 focus-visible:outline-2 focus-visible:outline-navy"
            style={{
              background: "white",
              border: "1.5px solid rgba(7,24,73,0.15)",
              color: "#071849",
              boxShadow: "0 4px 16px rgba(7,24,73,0.06)",
            }}
          >
            TALK TO OUR AI
          </a>
        </motion.div>
      </div>
    </section>
  );
}

function ExpIcon({ name, color }: { name: string; color: string }) {
  const icons: Record<string, React.ReactElement> = {
    MicIcon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
        <rect x="7" y="2" width="8" height="11" rx="4" stroke={color} strokeWidth="1.4" fill="none" />
        <path d="M4 11C4 15.4 7 18 11 18C15 18 18 15.4 18 11" stroke={color} strokeWidth="1.4" strokeLinecap="round" fill="none" />
        <line x1="11" y1="18" x2="11" y2="21" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
        <line x1="7" y1="21" x2="15" y2="21" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
      </svg>
    ),
    FlowIcon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
        <circle cx="5" cy="5" r="3" stroke={color} strokeWidth="1.3" fill="none" />
        <circle cx="17" cy="5" r="3" stroke={color} strokeWidth="1.3" fill="none" />
        <circle cx="11" cy="17" r="3" stroke={color} strokeWidth="1.3" fill="none" />
        <path d="M8 5h6M14 7l-3 7M8 7l3 7" stroke={color} strokeWidth="1.1" strokeLinecap="round" />
      </svg>
    ),
    TeamIcon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
        <circle cx="8" cy="7" r="3" stroke={color} strokeWidth="1.3" fill="none" />
        <circle cx="15" cy="7" r="2.5" stroke={color} strokeWidth="1.1" fill="none" />
        <path d="M2 19s1-5 6-5 6 5 6 5" stroke={color} strokeWidth="1.3" strokeLinecap="round" fill="none" />
        <path d="M15 13c3 0 5 2 5 5" stroke={color} strokeWidth="1.1" strokeLinecap="round" fill="none" />
      </svg>
    ),
  };
  return icons[name] ?? null;
}

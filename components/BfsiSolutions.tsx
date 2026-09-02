"use client";

import React, { useRef } from "react";
import { motion, useInView } from "framer-motion";

const solutions = [
  {
    id: "collections",
    icon: "CollectionsIcon",
    title: "Collections",
    body: "Intelligent payment conversations that understand intent, commitments and next steps — turning difficult calls into structured outcomes.",
    accent: "#FF681A",
  },
  {
    id: "customer-service",
    icon: "ServiceIcon",
    title: "Customer Service",
    body: "Resolve routine customer conversations naturally while escalating complex cases to human agents at the right moment.",
    accent: "#1E6FD9",
  },
  {
    id: "loan-credit",
    icon: "LoanIcon",
    title: "Loan & Credit",
    body: "Qualify, engage and assist customers throughout the lending journey — from initial inquiry to documentation follow-up.",
    accent: "#16A34A",
  },
  {
    id: "insurance",
    icon: "InsuranceIcon",
    title: "Insurance",
    body: "Automate renewal reminders, policy conversations and customer engagement across your insurance portfolio.",
    accent: "#1E6FD9",
  },
  {
    id: "verification",
    icon: "VerifyIcon",
    title: "Verification",
    body: "Support secure, structured voice workflows for KYC, identity confirmation and compliance-sensitive interactions.",
    accent: "#FF681A",
  },
  {
    id: "sales",
    icon: "SalesIcon",
    title: "Sales",
    body: "Turn customer conversations into qualified opportunities — identifying intent, capturing interest and driving the next action.",
    accent: "#16A34A",
  },
];

export default function BfsiSolutions() {
  const ref = useRef<HTMLElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      id="bfsi-solutions"
      className="relative py-24 lg:py-36"
      style={{ background: "white" }}
      aria-label="BFSI Solutions"
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
            Act 06 — BFSI Workflows
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight"
            style={{ color: "#071849" }}
          >
            Built for India&apos;s
            <br />
            <span style={{ color: "#FF681A" }}>financial conversations.</span>
          </motion.h2>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {solutions.map((sol, i) => (
            <motion.article
              key={sol.id}
              initial={{ opacity: 0, y: 24 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: 0.15 + i * 0.08 }}
              className="relative p-7 rounded-2xl group cursor-default transition-all duration-300 hover:-translate-y-1"
              style={{
                background: "#F3F6FA",
                border: "1px solid rgba(7,24,73,0.08)",
              }}
            >
              {/* Hover border accent */}
              <div
                className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
                style={{
                  border: `1px solid ${sol.accent}40`,
                  boxShadow: `0 8px 32px ${sol.accent}12`,
                }}
              />

              {/* Icon */}
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center mb-5"
                style={{
                  background: `${sol.accent}12`,
                  border: `1px solid ${sol.accent}25`,
                }}
              >
                <SolutionIcon name={sol.icon} color={sol.accent} />
              </div>

              {/* Label */}
              <div
                className="text-xs font-bold tracking-widest uppercase mb-2"
                style={{ color: sol.accent }}
              >
                {sol.title}
              </div>

              {/* Body */}
              <p className="text-sm leading-relaxed" style={{ color: "#4B5880" }}>
                {sol.body}
              </p>

              {/* Hover arrow */}
              <motion.div
                className="mt-5 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
              >
                <span className="text-xs font-semibold" style={{ color: sol.accent }}>
                  Learn more →
                </span>
              </motion.div>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}

function SolutionIcon({ name, color }: { name: string; color: string }) {
  const icons: Record<string, React.ReactElement> = {
    CollectionsIcon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <path d="M3 10h14M3 6h14M3 14h8" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="15" cy="14" r="3" stroke={color} strokeWidth="1.3" fill="none" />
        <path d="M15 13v1.5l1 .5" stroke={color} strokeWidth="1.1" strokeLinecap="round" />
      </svg>
    ),
    ServiceIcon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <path d="M4 4h12a1 1 0 011 1v7a1 1 0 01-1 1H6l-3 3V5a1 1 0 011-1z" stroke={color} strokeWidth="1.3" fill="none" />
        <circle cx="7.5" cy="8" r="1" fill={color} />
        <circle cx="10" cy="8" r="1" fill={color} />
        <circle cx="12.5" cy="8" r="1" fill={color} />
      </svg>
    ),
    LoanIcon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <rect x="2" y="5" width="16" height="11" rx="2" stroke={color} strokeWidth="1.3" fill="none" />
        <path d="M2 9h16" stroke={color} strokeWidth="1.3" />
        <path d="M6 13h3M13 13h1" stroke={color} strokeWidth="1.3" strokeLinecap="round" />
        <path d="M10 2v3" stroke={color} strokeWidth="1.3" strokeLinecap="round" />
      </svg>
    ),
    InsuranceIcon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <path d="M10 2L3 5v6c0 4 3.5 7 7 7s7-3 7-7V5L10 2z" stroke={color} strokeWidth="1.3" fill="none" />
        <path d="M7 10l2 2 4-4" stroke={color} strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    VerifyIcon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <circle cx="10" cy="8" r="4" stroke={color} strokeWidth="1.3" fill="none" />
        <path d="M4 17s1-4 6-4 6 4 6 4" stroke={color} strokeWidth="1.3" strokeLinecap="round" fill="none" />
        <path d="M13 4l1.5 1.5L17 3" stroke={color} strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    SalesIcon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <path d="M4 15l4-5 3 3 5-7" stroke={color} strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        <circle cx="16" cy="5" r="2" fill={color} opacity="0.4" />
        <path d="M4 18h12" stroke={color} strokeWidth="1.3" strokeLinecap="round" />
      </svg>
    ),
  };

  return icons[name] ?? null;
}

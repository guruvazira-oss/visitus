"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";

const architectureFlow = [
  { label: "CUSTOMER", sub: "Voice Interaction", color: "#FF681A", icon: "👤" },
  { label: "VOICE INDIA", sub: "Voice Intelligence Layer", color: "#1E6FD9", icon: "◈" },
  { label: "AI AGENT", sub: "Decision & Action Engine", color: "#3B9EFF", icon: "⬡" },
  { label: "ENTERPRISE WORKFLOW", sub: "Integrated Business Process", color: "#071849", icon: "⊞" },
  { label: "BUSINESS OUTCOME", sub: "Measurable Results", color: "#16A34A", icon: "✓" },
];

const integrations = [
  { label: "CRM", color: "#FF681A" },
  { label: "LOS", color: "#1E6FD9" },
  { label: "CBS", color: "#16A34A" },
  { label: "Ticketing", color: "#FF681A" },
  { label: "APIs", color: "#1E6FD9" },
  { label: "Payments", color: "#16A34A" },
];

export default function EnterpriseArchitecture() {
  const ref = useRef<HTMLElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      id="platform"
      className="relative py-24 lg:py-36 overflow-hidden"
      style={{ background: "#F3F6FA" }}
      aria-label="Enterprise architecture"
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">
          <div>
            <motion.span
              initial={{ opacity: 0, y: 10 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5 }}
              className="inline-block text-xs font-semibold tracking-widest uppercase mb-4"
              style={{ color: "#FF681A" }}
            >
              Act 07 — The Platform
            </motion.span>
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight"
              style={{ color: "#071849" }}
            >
              Your systems.
              <br />
              <span style={{ color: "#FF681A" }}>Our intelligence.</span>
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="mt-6 text-lg leading-relaxed"
              style={{ color: "#4B5880" }}
            >
              Voice India connects seamlessly with your existing enterprise
              infrastructure — adding voice intelligence without disrupting your
              workflows.
            </motion.p>

            {/* Integration chips */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.35 }}
              className="mt-10"
            >
              <p
                className="text-xs font-semibold tracking-widest uppercase mb-4"
                style={{ color: "#6B7BA8" }}
              >
                Connects with
              </p>
              <div className="flex flex-wrap gap-3">
                {integrations.map((int, i) => (
                  <motion.span
                    key={int.label}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={isInView ? { opacity: 1, scale: 1 } : {}}
                    transition={{ duration: 0.4, delay: 0.4 + i * 0.06 }}
                    className="px-4 py-2 rounded-full text-sm font-semibold"
                    style={{
                      background: `${int.color}10`,
                      border: `1px solid ${int.color}30`,
                      color: int.color,
                    }}
                  >
                    {int.label}
                  </motion.span>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Architecture diagram */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="flex flex-col items-center"
          >
            {architectureFlow.map((node, i) => (
              <div key={node.label} className="flex flex-col items-center w-full">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={isInView ? { opacity: 1, y: 0 } : {}}
                  transition={{ duration: 0.5, delay: 0.4 + i * 0.12 }}
                  className="w-full max-w-sm px-6 py-4 rounded-2xl flex items-center gap-4"
                  style={{
                    background:
                      i === 1
                        ? "linear-gradient(135deg, rgba(30,111,217,0.12) 0%, rgba(59,158,255,0.08) 100%)"
                        : "white",
                    border:
                      i === 1
                        ? "1.5px solid rgba(30,111,217,0.3)"
                        : "1px solid rgba(7,24,73,0.08)",
                    boxShadow:
                      i === 1
                        ? "0 4px 24px rgba(30,111,217,0.12)"
                        : "0 2px 8px rgba(7,24,73,0.05)",
                  }}
                >
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 text-base font-bold"
                    style={{
                      background: `${node.color}15`,
                      border: `1.5px solid ${node.color}40`,
                      color: node.color,
                    }}
                  >
                    {node.icon}
                  </div>
                  <div>
                    <div
                      className="text-xs font-bold tracking-widest uppercase"
                      style={{ color: node.color }}
                    >
                      {node.label}
                    </div>
                    <div
                      className="text-xs mt-0.5"
                      style={{ color: "#6B7BA8" }}
                    >
                      {node.sub}
                    </div>
                  </div>

                  {i === 1 && (
                    <div className="ml-auto">
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ background: "#16A34A" }}
                      />
                    </div>
                  )}
                </motion.div>

                {/* Connector line with animated pulse */}
                {i < architectureFlow.length - 1 && (
                  <div className="w-px h-8 relative my-1">
                    <div
                      className="absolute inset-0"
                      style={{
                        background: `linear-gradient(180deg, ${node.color}60, ${architectureFlow[i + 1].color}40)`,
                      }}
                    />
                    <motion.div
                      className="absolute left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full"
                      style={{ background: node.color, top: 0 }}
                      animate={{ top: ["0%", "100%"] }}
                      transition={{
                        duration: 1.2,
                        repeat: Infinity,
                        delay: i * 0.3,
                        ease: "linear",
                      }}
                    />
                  </div>
                )}
              </div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
}

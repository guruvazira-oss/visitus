"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import Image from "next/image";

export default function FinalCTA() {
  const ref = useRef<HTMLElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      className="relative min-h-[70vh] flex items-center overflow-hidden"
      style={{ background: "#071849" }}
      aria-label="Final call to action"
    >
      {/* Background */}
      <div className="absolute inset-0 z-0">
        <Image
          src="/assets/voice-india-gff-background.svg"
          alt=""
          fill
          style={{
            objectFit: "cover",
            objectPosition: "center bottom",
            opacity: 0.35,
            filter: "brightness(0.3) saturate(0.7)",
          }}
          aria-hidden="true"
        />
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(180deg, rgba(7,24,73,0.7) 0%, rgba(7,24,73,0.4) 50%, rgba(7,24,73,0.8) 100%)",
          }}
        />
      </div>

      {/* Animated particles */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        {[...Array(16)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full"
            style={{
              width: Math.random() * 3 + 1.5,
              height: Math.random() * 3 + 1.5,
              left: `${6 + i * 6}%`,
              top: `${15 + (i % 6) * 13}%`,
              background:
                i % 3 === 0
                  ? "rgba(255,104,26,0.7)"
                  : i % 3 === 1
                  ? "rgba(255,255,255,0.4)"
                  : "rgba(59,158,255,0.5)",
            }}
            animate={{
              y: [0, -20, 0],
              opacity: [0.3, 0.8, 0.3],
            }}
            transition={{
              duration: 5 + (i % 4),
              repeat: Infinity,
              delay: i * 0.5,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-4xl mx-auto px-6 lg:px-8 py-24 text-center">
        <motion.span
          initial={{ opacity: 0, y: 10 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="inline-block text-xs font-semibold tracking-widest uppercase mb-8"
          style={{ color: "#FF681A" }}
        >
          Act 11 — Call to Action
        </motion.span>

        <motion.h2
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-5xl sm:text-6xl lg:text-7xl xl:text-8xl font-bold leading-tight"
        >
          <span style={{ color: "white" }}>India is ready</span>
          <br />
          <span style={{ color: "white" }}>to talk.</span>
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-6 text-3xl sm:text-4xl font-bold"
          style={{ color: "#FF681A" }}
        >
          Are you ready for AI to talk back?
        </motion.p>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-8 text-lg"
          style={{ color: "rgba(255,255,255,0.7)" }}
        >
          Meet Voice India at Global Fintech Fest 2026.
          <br />
          <span style={{ color: "rgba(255,255,255,0.55)" }}>
            08–11 September · Jio World Centre, Mumbai
          </span>
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.55 }}
          className="flex flex-wrap gap-4 justify-center mt-12"
        >
          <a
            href="#book-meeting"
            className="inline-flex items-center gap-2.5 px-10 py-5 rounded-full text-sm font-bold tracking-wide text-white transition-all duration-200 hover:scale-105 focus-visible:outline-2 focus-visible:outline-orange-400"
            style={{
              background: "linear-gradient(135deg, #FF681A 0%, #E85500 100%)",
              boxShadow: "0 8px 40px rgba(255,104,26,0.5)",
            }}
          >
            MEET VOICE INDIA
          </a>
          <a
            href="#conversation-demo"
            className="inline-flex items-center gap-2.5 px-10 py-5 rounded-full text-sm font-bold tracking-wide transition-all duration-200 hover:scale-105 focus-visible:outline-2 focus-visible:outline-white"
            style={{
              background: "rgba(255,255,255,0.08)",
              backdropFilter: "blur(12px)",
              border: "1.5px solid rgba(255,255,255,0.25)",
              color: "white",
            }}
          >
            TALK TO OUR AI
          </a>
        </motion.div>

        {/* Logo mark */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="mt-16 flex items-center justify-center gap-3"
        >
          <svg
            width="36"
            height="36"
            viewBox="0 0 32 32"
            fill="none"
            aria-hidden="true"
          >
            <circle
              cx="16"
              cy="16"
              r="15"
              stroke="rgba(255,255,255,0.25)"
              strokeWidth="1"
              fill="none"
            />
            <path
              d="M8 16 Q10 12 12 16 Q14 20 16 16 Q18 12 20 16 Q22 20 24 16"
              stroke="rgba(255,255,255,0.7)"
              strokeWidth="1.8"
              fill="none"
              strokeLinecap="round"
            />
            <circle cx="27" cy="9" r="3" fill="#FF681A" />
          </svg>
          <span
            className="text-sm font-bold tracking-widest uppercase"
            style={{ color: "rgba(255,255,255,0.6)" }}
          >
            Voice India
          </span>
        </motion.div>
      </div>
    </section>
  );
}

"use client";

import { motion } from "framer-motion";
import { useRef } from "react";
import { useInView } from "framer-motion";

const languages = [
  { name: "Hindi", script: "हिंदी", size: "2xl" },
  { name: "Hinglish", script: "Hinglish", size: "xl" },
  { name: "Tamil", script: "தமிழ்", size: "2xl" },
  { name: "Telugu", script: "తెలుగు", size: "xl" },
  { name: "Kannada", script: "ಕನ್ನಡ", size: "xl" },
  { name: "Marathi", script: "मराठी", size: "2xl" },
  { name: "Bengali", script: "বাংলা", size: "xl" },
  { name: "Malayalam", script: "മലയാളം", size: "lg" },
  { name: "Gujarati", script: "ગુજરાતી", size: "xl" },
  { name: "Punjabi", script: "ਪੰਜਾਬੀ", size: "lg" },
  { name: "English", script: "English", size: "xl" },
];

export default function IndiaVoiceSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section
      ref={ref}
      id="why-voice-ai"
      className="relative py-24 lg:py-36 overflow-hidden"
      style={{ background: "#F3F6FA" }}
      aria-label="India's voice — multilingual intelligence"
    >
      {/* Background wave decoration */}
      <div
        className="absolute bottom-0 left-0 right-0 h-64 pointer-events-none"
        style={{
          background:
            "linear-gradient(180deg, transparent 0%, rgba(7,24,73,0.04) 100%)",
        }}
      />

      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <div className="max-w-3xl mb-16">
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5 }}
            className="inline-block text-xs font-semibold tracking-widest uppercase mb-4"
            style={{ color: "#FF681A" }}
          >
            Act 02 — The Problem
          </motion.span>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight"
            style={{ color: "#071849" }}
          >
            India doesn&apos;t just communicate.
            <br />
            <span style={{ color: "#FF681A" }}>India converses.</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-6 text-xl leading-relaxed"
            style={{ color: "#4B5880" }}
          >
            Customers switch languages. They interrupt. They change direction.
            They mix English with Hindi. They speak naturally.
            <br />
            <br />
            Enterprise AI must understand that reality.
          </motion.p>
        </div>

        {/* Language visualization */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="mb-16"
        >
          <p
            className="text-sm font-semibold tracking-widest uppercase mb-8"
            style={{ color: "#071849", opacity: 0.6 }}
          >
            AI that understands the way India actually speaks.
          </p>

          <div className="flex flex-wrap gap-4 items-baseline">
            {languages.map((lang, i) => (
              <motion.div
                key={lang.name}
                initial={{ opacity: 0, y: 20 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.5, delay: 0.1 + i * 0.06 }}
                className="flex flex-col items-center group cursor-default"
              >
                <span
                  className={`font-bold transition-colors duration-300 group-hover:text-orange-500`}
                  style={{
                    fontSize:
                      lang.size === "2xl"
                        ? "2rem"
                        : lang.size === "xl"
                        ? "1.5rem"
                        : "1.2rem",
                    color: i % 4 === 0 ? "#071849" : i % 4 === 1 ? "#102A5C" : i % 4 === 2 ? "#1E4A8C" : "#071849",
                    opacity: 0.7 + (i % 3) * 0.1,
                  }}
                >
                  {lang.script}
                </span>
                <span
                  className="text-xs tracking-wider mt-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                  style={{ color: "#FF681A" }}
                >
                  {lang.name}
                </span>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* The insight cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              title: "Natural Language",
              body: "People don't speak in forms. They express. AI must handle this.",
              icon: "💬",
            },
            {
              title: "Code Switching",
              body: "Moving between Hindi, English and regional languages in the same sentence.",
              icon: "🔄",
            },
            {
              title: "Conversational Intent",
              body: "Extracting meaning from natural, unstructured dialogue — not just keywords.",
              icon: "🧠",
            },
          ].map((card, i) => (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: 0.5 + i * 0.1 }}
              className="p-6 rounded-2xl group transition-all duration-300 hover:-translate-y-1"
              style={{
                background: "white",
                border: "1px solid rgba(7,24,73,0.08)",
                boxShadow: "0 2px 16px rgba(7,24,73,0.05)",
              }}
            >
              <span className="text-2xl mb-4 block" aria-hidden="true">
                {card.icon}
              </span>
              <h3
                className="text-lg font-bold mb-2"
                style={{ color: "#071849" }}
              >
                {card.title}
              </h3>
              <p className="text-sm leading-relaxed" style={{ color: "#6B7BA8" }}>
                {card.body}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

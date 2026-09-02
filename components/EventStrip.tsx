"use client";

import { motion } from "framer-motion";

const details = [
  { label: "08–11 SEP 2026", sub: "Event Dates" },
  { label: "Jio World Centre", sub: "Mumbai, India" },
  { label: "BKC, Mumbai", sub: "Bandra Kurla Complex" },
  { label: "GFF 2026", sub: "Global Fintech Fest" },
];

export default function EventStrip() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6 }}
      className="relative z-10"
      aria-label="Event details"
    >
      <div
        className="max-w-7xl mx-auto mx-6 lg:mx-8 px-6 lg:px-8"
        style={{ marginTop: "-1px" }}
      >
        <div
          className="flex flex-wrap md:flex-nowrap items-center justify-between px-6 lg:px-10 py-4"
          style={{
            background: "rgba(255,255,255,0.95)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(7,24,73,0.1)",
            borderRadius: "16px",
            boxShadow: "0 8px 32px rgba(7,24,73,0.08)",
          }}
        >
          {details.map((item, i) => (
            <div key={item.label} className="flex items-center gap-4">
              {i > 0 && (
                <div
                  className="hidden md:block w-px h-8"
                  style={{ background: "rgba(7,24,73,0.12)" }}
                  aria-hidden="true"
                />
              )}
              <div className="flex flex-col items-center py-2 px-4">
                <span
                  className="text-sm font-bold tracking-widest uppercase"
                  style={{ color: "#071849" }}
                >
                  {item.label}
                </span>
                <span
                  className="text-xs mt-0.5 tracking-wider"
                  style={{ color: "#6B7BA8" }}
                >
                  {item.sub}
                </span>
              </div>
            </div>
          ))}

          {/* India flag dots */}
          <div className="flex items-center gap-2 ml-auto md:ml-0">
            <div className="flex gap-1.5" aria-label="India flag colors">
              <span className="w-2 h-2 rounded-full" style={{ background: "#FF681A" }} />
              <span className="w-2 h-2 rounded-full" style={{ background: "#FFFFFF", border: "1px solid #ccc" }} />
              <span className="w-2 h-2 rounded-full" style={{ background: "#16A34A" }} />
            </div>
            <span className="text-xs font-medium" style={{ color: "#071849" }}>
              Made in India
            </span>
          </div>
        </div>
      </div>
    </motion.section>
  );
}

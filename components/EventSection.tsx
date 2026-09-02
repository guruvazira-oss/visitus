"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";

export default function EventSection() {
  const ref = useRef<HTMLElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      className="relative py-20"
      style={{ background: "white" }}
      aria-label="GFF 2026 event details"
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div
          className="rounded-3xl p-10 lg:p-16 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center"
          style={{
            background: "linear-gradient(135deg, #F3F8FF 0%, #EEF3FA 100%)",
            border: "1px solid rgba(7,24,73,0.08)",
          }}
        >
          {/* Event info */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.6 }}
          >
            <div
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold tracking-widest uppercase mb-6"
              style={{
                background: "rgba(255,104,26,0.1)",
                border: "1px solid rgba(255,104,26,0.3)",
                color: "#FF681A",
              }}
            >
              Global Fintech Fest 2026
            </div>

            <h2
              className="text-3xl sm:text-4xl font-bold mb-6 leading-tight"
              style={{ color: "#071849" }}
            >
              Find us at GFF 2026
            </h2>

            <div className="space-y-4">
              {[
                { label: "Dates", value: "08–11 September 2026" },
                {
                  label: "Venue",
                  value: "Jio World Centre, Bandra Kurla Complex, Mumbai",
                },
                { label: "Booth", value: "Details coming soon" },
              ].map((item) => (
                <div
                  key={item.label}
                  className="flex items-start gap-4 pb-4"
                  style={{ borderBottom: "1px solid rgba(7,24,73,0.06)" }}
                >
                  <div
                    className="text-xs font-bold tracking-widest uppercase w-16 flex-shrink-0 mt-0.5"
                    style={{ color: "#9BA8C8" }}
                  >
                    {item.label}
                  </div>
                  <div className="text-sm font-semibold" style={{ color: "#071849" }}>
                    {item.value}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* CTA box */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="flex flex-col gap-6"
          >
            <div
              className="p-8 rounded-2xl"
              style={{
                background: "#071849",
              }}
            >
              <h3
                className="text-2xl font-bold mb-3"
                style={{ color: "white" }}
              >
                Schedule a meeting
              </h3>
              <p
                className="text-sm mb-6 leading-relaxed"
                style={{ color: "rgba(255,255,255,0.65)" }}
              >
                Meet the Voice India team at GFF 2026. Share your use case and
                explore how enterprise voice intelligence applies to your
                organisation.
              </p>
              <a
                id="book-meeting"
                href="https://voiceindia.ai"
                target="_blank"
                rel="noopener noreferrer"
                className="w-full inline-flex items-center justify-center gap-2 px-6 py-4 rounded-full text-sm font-bold text-white transition-all duration-200 hover:scale-105 focus-visible:outline-2 focus-visible:outline-orange-400"
                style={{
                  background: "linear-gradient(135deg, #FF681A 0%, #E85500 100%)",
                  boxShadow: "0 8px 24px rgba(255,104,26,0.35)",
                }}
              >
                BOOK A MEETING
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                  aria-hidden="true"
                >
                  <path
                    d="M3 8h10M9 4l4 4-4 4"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </a>
            </div>

            <div
              className="p-6 rounded-2xl text-center"
              style={{
                background: "rgba(7,24,73,0.04)",
                border: "1px solid rgba(7,24,73,0.08)",
              }}
            >
              <p className="text-xs" style={{ color: "#6B7BA8" }}>
                Or visit{" "}
                <a
                  href="https://voiceindia.ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-semibold hover:underline"
                  style={{ color: "#071849" }}
                >
                  voiceindia.ai
                </a>{" "}
                to learn more
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

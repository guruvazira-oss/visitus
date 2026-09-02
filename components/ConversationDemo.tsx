"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useInView } from "framer-motion";

const demoFlow = [
  {
    type: "customer",
    text: '"Sir, mera EMI kal ho jayega."',
    subtext: "Customer • Hinglish",
    delay: 0,
  },
  {
    type: "ai",
    text: '"Understood. I\'ve recorded tomorrow as your payment commitment date."',
    subtext: "Voice India AI • Response",
    delay: 1200,
  },
];

const workflowSteps = [
  {
    label: "INTENT DETECTED",
    value: "Promise to Pay",
    icon: "🎯",
    color: "#16A34A",
    delay: 2600,
  },
  {
    label: "ACTION",
    value: "CRM Updated",
    icon: "⚡",
    color: "#1E6FD9",
    delay: 3000,
  },
  {
    label: "WORKFLOW",
    value: "Follow-up Scheduled",
    icon: "📅",
    color: "#FF681A",
    delay: 3400,
  },
  {
    label: "OUTCOME",
    value: "Collection Workflow Updated",
    icon: "✅",
    color: "#16A34A",
    delay: 3800,
  },
];

const pipeline = ["VOICE", "INTENT", "DECISION", "ACTION", "OUTCOME"];

export default function ConversationDemo() {
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const ref = useRef<HTMLElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  useEffect(() => {
    if (isInView && !playing) {
      setPlaying(true);
    }
  }, [isInView, playing]);

  useEffect(() => {
    if (!playing) return;
    const timers: ReturnType<typeof setTimeout>[] = [];

    timers.push(setTimeout(() => setStep(1), 500));
    timers.push(setTimeout(() => setStep(2), 1700));
    timers.push(setTimeout(() => setStep(3), 2700));
    timers.push(setTimeout(() => setStep(4), 3100));
    timers.push(setTimeout(() => setStep(5), 3500));
    timers.push(setTimeout(() => setStep(6), 3900));

    return () => timers.forEach(clearTimeout);
  }, [playing]);

  const restart = () => {
    setStep(0);
    setPlaying(false);
    setTimeout(() => setPlaying(true), 100);
  };

  return (
    <section
      ref={ref}
      id="conversation-demo"
      className="relative py-24 lg:py-36 overflow-hidden"
      aria-label="Conversation to action demo"
      style={{ background: "#071849" }}
    >
      {/* Background wave decoration */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 80% 60% at 50% 100%, rgba(16,42,92,0.8) 0%, rgba(7,24,73,0) 70%)",
          }}
        />
        {/* Tech dots */}
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full"
            style={{
              width: 2,
              height: 2,
              left: `${5 + i * 5}%`,
              top: `${20 + (i % 6) * 12}%`,
              background: "rgba(59,158,255,0.4)",
            }}
            animate={{ opacity: [0.2, 0.8, 0.2] }}
            transition={{ duration: 3 + (i % 3), repeat: Infinity, delay: i * 0.3 }}
          />
        ))}
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <div className="max-w-3xl mb-16">
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5 }}
            className="inline-block text-xs font-semibold tracking-widest uppercase mb-4"
            style={{ color: "#FF681A" }}
          >
            Act 05 — The Conversation
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight"
            style={{ color: "white" }}
          >
            From conversation
            <br />
            <span style={{ color: "#FF681A" }}>to action.</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-6 text-lg"
            style={{ color: "rgba(255,255,255,0.65)" }}
          >
            Voice India is not merely a chatbot. It is an AI agent that
            participates in enterprise workflows.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
          {/* Conversation UI */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <div
              className="rounded-2xl overflow-hidden"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.1)",
              }}
            >
              {/* Chat header */}
              <div
                className="px-5 py-4 flex items-center justify-between"
                style={{
                  background: "rgba(255,255,255,0.06)",
                  borderBottom: "1px solid rgba(255,255,255,0.08)",
                }}
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center"
                    style={{ background: "rgba(255,104,26,0.2)" }}
                  >
                    <WaveIcon small />
                  </div>
                  <div>
                    <div
                      className="text-sm font-semibold"
                      style={{ color: "white" }}
                    >
                      Voice India AI
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span
                        className="w-1.5 h-1.5 rounded-full"
                        style={{ background: "#16A34A" }}
                      />
                      <span className="text-xs" style={{ color: "#16A34A" }}>
                        Active
                      </span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={restart}
                  className="text-xs px-3 py-1.5 rounded-full transition-all duration-200 hover:scale-105"
                  style={{
                    background: "rgba(255,104,26,0.15)",
                    border: "1px solid rgba(255,104,26,0.3)",
                    color: "#FF681A",
                  }}
                  aria-label="Replay conversation demo"
                >
                  ↺ Replay
                </button>
              </div>

              {/* Messages */}
              <div className="p-5 space-y-4 min-h-[220px]">
                <AnimatePresence>
                  {step >= 1 && (
                    <motion.div
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4 }}
                      className="flex gap-3 justify-end"
                    >
                      <div className="max-w-xs">
                        <div
                          className="px-4 py-3 rounded-2xl rounded-tr-sm text-sm leading-relaxed"
                          style={{
                            background: "rgba(255,255,255,0.08)",
                            color: "rgba(255,255,255,0.9)",
                          }}
                        >
                          {demoFlow[0].text}
                        </div>
                        <p
                          className="text-right text-xs mt-1"
                          style={{ color: "rgba(255,255,255,0.35)" }}
                        >
                          {demoFlow[0].subtext}
                        </p>
                      </div>
                    </motion.div>
                  )}

                  {step >= 2 && (
                    <motion.div
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4 }}
                      className="flex gap-3"
                    >
                      <div
                        className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center"
                        style={{ background: "rgba(30,111,217,0.2)" }}
                      >
                        <WaveIcon small />
                      </div>
                      <div className="max-w-xs">
                        <div
                          className="px-4 py-3 rounded-2xl rounded-tl-sm text-sm leading-relaxed"
                          style={{
                            background: "rgba(30,111,217,0.15)",
                            border: "1px solid rgba(30,111,217,0.25)",
                            color: "rgba(255,255,255,0.9)",
                          }}
                        >
                          {demoFlow[1].text}
                        </div>
                        <p
                          className="text-xs mt-1"
                          style={{ color: "rgba(255,255,255,0.35)" }}
                        >
                          {demoFlow[1].subtext}
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {step < 1 && (
                  <div className="flex items-center justify-center h-32">
                    <motion.div
                      animate={{ opacity: [0.3, 0.8, 0.3] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                      className="text-sm"
                      style={{ color: "rgba(255,255,255,0.4)" }}
                    >
                      Starting conversation…
                    </motion.div>
                  </div>
                )}
              </div>

              {/* Workflow results */}
              <div
                className="p-5 space-y-3"
                style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
              >
                <AnimatePresence>
                  {workflowSteps.map(
                    (ws, i) =>
                      step >= i + 3 && (
                        <motion.div
                          key={ws.label}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.35 }}
                          className="flex items-center gap-3 px-4 py-3 rounded-xl"
                          style={{
                            background: `${ws.color}10`,
                            border: `1px solid ${ws.color}30`,
                          }}
                        >
                          <span className="text-base" aria-hidden="true">
                            {ws.icon}
                          </span>
                          <div className="flex-1">
                            <div
                              className="text-xs font-bold tracking-widest uppercase"
                              style={{ color: ws.color }}
                            >
                              {ws.label}
                            </div>
                            <div
                              className="text-sm font-medium"
                              style={{ color: "rgba(255,255,255,0.85)" }}
                            >
                              {ws.value}
                            </div>
                          </div>
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ type: "spring", stiffness: 400 }}
                          >
                            <svg
                              width="16"
                              height="16"
                              viewBox="0 0 16 16"
                              fill="none"
                              aria-hidden="true"
                            >
                              <circle cx="8" cy="8" r="7" fill={ws.color} opacity="0.2" />
                              <path
                                d="M5 8l2 2 4-4"
                                stroke={ws.color}
                                strokeWidth="1.5"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                              />
                            </svg>
                          </motion.div>
                        </motion.div>
                      )
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>

          {/* Pipeline visualization */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="flex flex-col gap-0 items-center"
          >
            <p
              className="text-xs font-semibold tracking-widest uppercase mb-8 text-center"
              style={{ color: "rgba(255,255,255,0.4)" }}
            >
              The Voice India Intelligence Pipeline
            </p>

            {pipeline.map((label, i) => {
              const isActive = step >= i + 1;
              return (
                <div key={label} className="flex flex-col items-center w-full max-w-xs">
                  <motion.div
                    initial={{ opacity: 0.3, scale: 0.95 }}
                    animate={
                      isActive
                        ? { opacity: 1, scale: 1 }
                        : { opacity: 0.3, scale: 0.95 }
                    }
                    transition={{ duration: 0.3 }}
                    className="w-full px-8 py-4 rounded-2xl text-center font-bold tracking-widest text-sm"
                    style={{
                      background: isActive
                        ? i === 0
                          ? "rgba(255,104,26,0.15)"
                          : i === pipeline.length - 1
                          ? "rgba(22,163,74,0.15)"
                          : "rgba(30,111,217,0.15)"
                        : "rgba(255,255,255,0.04)",
                      border: `1px solid ${
                        isActive
                          ? i === 0
                            ? "rgba(255,104,26,0.4)"
                            : i === pipeline.length - 1
                            ? "rgba(22,163,74,0.4)"
                            : "rgba(30,111,217,0.4)"
                          : "rgba(255,255,255,0.08)"
                      }`,
                      color: isActive
                        ? i === 0
                          ? "#FF681A"
                          : i === pipeline.length - 1
                          ? "#16A34A"
                          : "#3B9EFF"
                        : "rgba(255,255,255,0.25)",
                    }}
                  >
                    {label}
                  </motion.div>

                  {i < pipeline.length - 1 && (
                    <motion.div
                      className="w-px h-8 my-1"
                      style={{
                        background: isActive
                          ? "linear-gradient(180deg, rgba(30,111,217,0.6), rgba(30,111,217,0.2))"
                          : "rgba(255,255,255,0.08)",
                      }}
                      animate={
                        isActive
                          ? { scaleY: [0.5, 1, 0.5], opacity: [0.5, 1, 0.5] }
                          : {}
                      }
                      transition={{ duration: 1.5, repeat: Infinity }}
                    />
                  )}
                </div>
              );
            })}
          </motion.div>
        </div>
      </div>
    </section>
  );
}

function WaveIcon({ small }: { small?: boolean }) {
  const size = small ? 16 : 24;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M3 12 Q5 8 7 12 Q9 16 11 12 Q13 8 15 12 Q17 16 19 12 Q21 8 21 12"
        stroke="#FF681A"
        strokeWidth="1.8"
        fill="none"
        strokeLinecap="round"
      />
    </svg>
  );
}

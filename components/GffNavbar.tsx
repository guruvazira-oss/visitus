"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

const navLinks = [
  { label: "Why Voice AI", href: "#why-voice-ai" },
  { label: "Solutions", href: "#bfsi-solutions" },
  { label: "Technology", href: "#platform" },
  { label: "GFF 2026", href: "#gff-experience" },
];

export default function GffNavbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
      style={{
        background: scrolled
          ? "rgba(255,255,255,0.92)"
          : "transparent",
        backdropFilter: scrolled ? "blur(16px)" : "none",
        borderBottom: scrolled ? "1px solid rgba(7,24,73,0.08)" : "none",
      }}
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link
          href="/gff-2026"
          className="flex items-center gap-2.5 group focus-visible:outline-orange-500"
          aria-label="Voice India - Home"
        >
          <VoiceIndiaLogo scrolled={scrolled} />
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-8" aria-label="Main navigation">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm font-medium tracking-wide transition-colors duration-200"
              style={{ color: scrolled ? "#071849" : "rgba(255,255,255,0.9)" }}
              onMouseEnter={(e) =>
                ((e.target as HTMLElement).style.color = "#FF681A")
              }
              onMouseLeave={(e) =>
                ((e.target as HTMLElement).style.color = scrolled
                  ? "#071849"
                  : "rgba(255,255,255,0.9)")
              }
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* CTA */}
        <div className="flex items-center gap-4">
          <a
            href="#book-meeting"
            className="hidden md:inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold text-white transition-all duration-200 hover:scale-105 focus-visible:outline-2 focus-visible:outline-orange-500"
            style={{
              background: "linear-gradient(135deg, #FF681A 0%, #E85500 100%)",
              boxShadow: "0 4px 16px rgba(255,104,26,0.3)",
            }}
          >
            Book a Meeting
          </a>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden p-2 rounded-lg"
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            aria-expanded={menuOpen}
          >
            <div className="w-5 flex flex-col gap-1.5">
              <span
                className="block h-0.5 rounded transition-all duration-300"
                style={{
                  background: scrolled ? "#071849" : "white",
                  transform: menuOpen ? "rotate(45deg) translate(5px, 5px)" : "",
                }}
              />
              <span
                className="block h-0.5 rounded transition-all duration-300"
                style={{
                  background: scrolled ? "#071849" : "white",
                  opacity: menuOpen ? 0 : 1,
                }}
              />
              <span
                className="block h-0.5 rounded transition-all duration-300"
                style={{
                  background: scrolled ? "#071849" : "white",
                  transform: menuOpen ? "rotate(-45deg) translate(5px, -5px)" : "",
                }}
              />
            </div>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
            className="md:hidden overflow-hidden"
            style={{
              background: "rgba(255,255,255,0.97)",
              backdropFilter: "blur(16px)",
              borderBottom: "1px solid rgba(7,24,73,0.08)",
            }}
          >
            <nav className="px-6 py-4 flex flex-col gap-4" aria-label="Mobile navigation">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMenuOpen(false)}
                  className="text-sm font-medium py-2 text-navy-800 border-b border-gray-100"
                  style={{ color: "#071849" }}
                >
                  {link.label}
                </a>
              ))}
              <a
                href="#book-meeting"
                onClick={() => setMenuOpen(false)}
                className="inline-flex items-center justify-center px-5 py-3 rounded-full text-sm font-semibold text-white mt-2"
                style={{
                  background: "linear-gradient(135deg, #FF681A 0%, #E85500 100%)",
                }}
              >
                Book a Meeting
              </a>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}

function VoiceIndiaLogo({ scrolled }: { scrolled: boolean }) {
  const color = scrolled ? "#071849" : "#FFFFFF";
  const accent = "#FF681A";

  return (
    <div className="flex items-center gap-2.5">
      {/* Icon mark */}
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <circle cx="16" cy="16" r="15" stroke={color} strokeWidth="1.5" fill="none" opacity="0.3" />
        {/* Wave lines representing voice */}
        <path
          d="M8 16 Q10 12 12 16 Q14 20 16 16 Q18 12 20 16 Q22 20 24 16"
          stroke={color}
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
        />
        {/* Dot accent */}
        <circle cx="27" cy="9" r="3" fill={accent} />
      </svg>

      {/* Wordmark */}
      <div className="flex flex-col leading-none">
        <span
          className="text-sm font-bold tracking-widest uppercase"
          style={{ color, letterSpacing: "0.15em" }}
        >
          Voice India
        </span>
        <span
          className="text-xs tracking-wider"
          style={{ color: scrolled ? "#FF681A" : "rgba(255,200,160,0.9)", letterSpacing: "0.08em" }}
        >
          voiceindia.ai
        </span>
      </div>
    </div>
  );
}

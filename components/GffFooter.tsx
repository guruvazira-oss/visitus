"use client";

const footerLinks = {
  Platform: ["Overview", "Voice Intelligence", "AI Agent", "Integrations"],
  Solutions: ["Collections", "Customer Service", "Loan & Credit", "Insurance"],
  Technology: ["Architecture", "Security", "Compliance", "Scalability"],
  "GFF 2026": ["Event Details", "Book a Meeting", "Talk to Our AI", "Contact"],
};

export default function GffFooter() {
  const year = new Date().getFullYear();

  return (
    <footer
      className="relative pt-16 pb-8 overflow-hidden"
      style={{ background: "#0A1F3D" }}
      aria-label="Site footer"
    >
      {/* Wave top decoration */}
      <div className="absolute top-0 left-0 right-0 pointer-events-none" aria-hidden="true">
        <svg
          viewBox="0 0 1440 60"
          className="w-full"
          preserveAspectRatio="none"
          fill="none"
        >
          <path
            d="M0 60 Q360 0 720 30 Q1080 60 1440 10 L1440 0 L0 0 Z"
            fill="rgba(7,24,73,0.4)"
          />
        </svg>
      </div>

      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Main footer grid */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-12 mb-12">
          {/* Brand */}
          <div className="md:col-span-2">
            {/* Logo */}
            <div className="flex items-center gap-2.5 mb-5">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
                <circle cx="16" cy="16" r="15" stroke="rgba(255,255,255,0.2)" strokeWidth="1" fill="none" />
                <path
                  d="M8 16 Q10 12 12 16 Q14 20 16 16 Q18 12 20 16 Q22 20 24 16"
                  stroke="rgba(255,255,255,0.7)"
                  strokeWidth="1.8"
                  fill="none"
                  strokeLinecap="round"
                />
                <circle cx="27" cy="9" r="3" fill="#FF681A" />
              </svg>
              <div>
                <div
                  className="text-sm font-bold tracking-widest uppercase"
                  style={{ color: "white", letterSpacing: "0.15em" }}
                >
                  Voice India
                </div>
                <div
                  className="text-xs"
                  style={{ color: "rgba(255,104,26,0.8)", letterSpacing: "0.06em" }}
                >
                  voiceindia.ai
                </div>
              </div>
            </div>

            <p
              className="text-sm leading-relaxed max-w-xs mb-6"
              style={{ color: "rgba(255,255,255,0.55)" }}
            >
              AI-Powered Conversations.
              <br />
              Stronger Outcomes.
            </p>

            {/* Social links */}
            <div className="flex gap-3" aria-label="Social links">
              {["LinkedIn", "X", "Website"].map((social) => (
                <a
                  key={social}
                  href="https://voiceindia.ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-200 hover:scale-110 text-xs font-medium"
                  style={{
                    background: "rgba(255,255,255,0.06)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    color: "rgba(255,255,255,0.55)",
                  }}
                  aria-label={social}
                >
                  {social[0]}
                </a>
              ))}
            </div>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h3
                className="text-xs font-bold tracking-widest uppercase mb-5"
                style={{ color: "rgba(255,255,255,0.4)" }}
              >
                {category}
              </h3>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link}>
                    <a
                      href="#"
                      className="text-sm transition-colors duration-200 hover:text-white"
                      style={{ color: "rgba(255,255,255,0.5)" }}
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div
          className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-8"
          style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
        >
          <p
            className="text-xs"
            style={{ color: "rgba(255,255,255,0.3)" }}
          >
            © {year} Voice India. All rights reserved.
          </p>
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5" aria-label="India flag colors">
              <span
                className="w-2 h-2 rounded-full"
                style={{ background: "#FF681A" }}
              />
              <span
                className="w-2 h-2 rounded-full"
                style={{
                  background: "#FFFFFF",
                  border: "1px solid rgba(255,255,255,0.2)",
                }}
              />
              <span
                className="w-2 h-2 rounded-full"
                style={{ background: "#16A34A" }}
              />
            </div>
            <p className="text-xs" style={{ color: "rgba(255,255,255,0.3)" }}>
              Proudly built in India
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}

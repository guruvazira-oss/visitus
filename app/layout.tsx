import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Voice India at Global Fintech Fest 2026 | AI-Powered Conversations",
  description:
    "Meet Voice India at Global Fintech Fest 2026 and experience enterprise AI voice agents built for India's conversations, workflows and customer outcomes.",
  openGraph: {
    title: "Voice India at Global Fintech Fest 2026 | AI-Powered Conversations",
    description:
      "Meet Voice India at Global Fintech Fest 2026 and experience enterprise AI voice agents built for India's conversations, workflows and customer outcomes.",
    type: "website",
    locale: "en_IN",
  },
  twitter: {
    card: "summary_large_image",
    title: "Voice India at GFF 2026",
    description:
      "Enterprise AI voice agents built for India's conversations.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}

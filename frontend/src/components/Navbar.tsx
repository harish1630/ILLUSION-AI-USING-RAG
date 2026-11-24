"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import {
  Sparkles,
  Globe,
  Menu,
  X,
  ArrowRight,
} from "lucide-react";

export default function Navbar() {
  const { language, toggleLanguage, t } = useLanguage();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { href: "/", label: t.nav.home },
    { href: "/marketplace", label: "Marketplace", badge: "Apps" },
    { href: "/onboarding", label: t.nav.onboarding },
    { href: "/schemes", label: t.nav.schemes },
    { href: "/tools", label: t.nav.tools || "AI Tools" },
    { href: "/github", label: "GitHub", badge: "Tools" },
    { href: "/chat", label: t.nav.chat },
    { href: "/roadmap", label: t.nav.roadmap },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#0D0D0E]/90 backdrop-blur-md border-b border-[#24242A]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Brand Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-lg bg-[#18181C] border border-[#2E2E36] group-hover:border-amber-500/50 flex items-center justify-center text-amber-400 shadow-sm transition-all">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-white font-sans flex items-center gap-1.5">
                illusion <span className="text-amber-400 font-extrabold">AI</span>
              </span>
              <span className="hidden sm:block text-[9px] text-zinc-500 font-mono tracking-widest uppercase">
                TN & Central MSME OS
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links - Always Visible */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all relative flex items-center gap-1.5 ${
                    isActive
                      ? "text-amber-400 bg-amber-500/10 border border-amber-500/30 font-semibold"
                      : "text-zinc-400 hover:text-white hover:bg-zinc-900 border border-transparent"
                  }`}
                >
                  {link.label}
                  {link.badge && (
                    <span className="px-1.5 py-0.2 bg-amber-500/20 text-amber-300 text-[10px] font-semibold rounded border border-amber-500/30">
                      {link.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Actions: Language Toggle & CTA */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={toggleLanguage}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-[#2E2E36] bg-[#151518] text-xs font-medium text-zinc-300 hover:text-white hover:border-zinc-500 transition-colors"
              title="Toggle Tamil / English"
            >
              <Globe className="w-3.5 h-3.5 text-amber-400" />
              <span>{t.nav.language}</span>
            </button>

            <Link
              href="/onboarding"
              className="hidden sm:inline-flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 text-black px-3.5 py-1.5 rounded-md text-xs font-semibold shadow-sm transition-all"
            >
              <span>{t.hero.primaryCta}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>

            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-md text-zinc-400 hover:text-white hover:bg-zinc-900"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5 text-zinc-200" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[#24242A] bg-[#0D0D0E] px-4 pt-2 pb-4 space-y-1">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium ${
                  isActive
                    ? "text-amber-400 bg-amber-500/10 font-semibold"
                    : "text-zinc-400 hover:text-white hover:bg-zinc-900"
                }`}
              >
                <span>{link.label}</span>
                {link.badge && (
                  <span className="px-1.5 py-0.5 bg-amber-500/20 text-amber-300 text-[10px] font-semibold rounded">
                    {link.badge}
                  </span>
                )}
              </Link>
            );
          })}

          <div className="pt-2 border-t border-[#24242A]">
            <Link
              href="/onboarding"
              onClick={() => setMobileMenuOpen(false)}
              className="w-full flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-black py-2 rounded-md text-sm font-semibold"
            >
              <span>{t.hero.primaryCta}</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}

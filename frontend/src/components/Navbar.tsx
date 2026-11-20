"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import { useAuth } from "@/context/AuthContext";
import {
  Sparkles,
  Globe,
  Menu,
  X,
  ArrowRight,
  User,
  LogOut,
  ChevronDown,
  Shield,
  Loader2,
} from "lucide-react";

export default function Navbar() {
  const { language, toggleLanguage, t } = useLanguage();
  const { user, isAuthenticated, isLoading, loginWithGoogle, logout } = useAuth();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setUserDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const navLinks = [
    { href: "/", label: t.nav.home },
    { href: "/onboarding", label: t.nav.onboarding },
    { href: "/schemes", label: t.nav.schemes },
    { href: "/tools", label: t.nav.tools || "AI Tools" },
    { href: "/mcp", label: "MCP Hub", badge: "MCP 2.0" },
    { href: "/github", label: "GitHub", badge: "OAuth" },
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

          {/* Desktop Navigation Links */}
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

          {/* Actions: Google Auth, Language Toggle & CTA */}
          <div className="hidden md:flex items-center gap-2.5">
            <button
              onClick={toggleLanguage}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-[#2E2E36] bg-[#151518] text-xs font-medium text-zinc-300 hover:text-white hover:border-zinc-500 transition-colors"
              title="Toggle Tamil / English"
            >
              <Globe className="w-3.5 h-3.5 text-amber-400" />
              <span>{t.nav.language}</span>
            </button>

            {/* Google OAuth State */}
            {isAuthenticated && user ? (
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                  className="flex items-center gap-2 px-2.5 py-1.5 rounded-md border border-[#2E2E36] bg-[#161619] hover:bg-[#1E1E24] text-xs font-medium text-zinc-200 transition-all"
                >
                  {user.picture ? (
                    <img
                      src={user.picture}
                      alt={user.name || "User"}
                      className="w-5 h-5 rounded-full object-cover border border-amber-500/40"
                    />
                  ) : (
                    <div className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold text-[10px]">
                      {(user.name || user.email || "U").charAt(0).toUpperCase()}
                    </div>
                  )}
                  <span className="max-w-[100px] truncate">{user.name || user.email.split("@")[0]}</span>
                  <ChevronDown className="w-3.5 h-3.5 text-zinc-400" />
                </button>

                {/* Dropdown Menu */}
                {userDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 rounded-xl bg-[#141417] border border-[#2B2B33] shadow-2xl py-1.5 z-50 text-xs">
                    <div className="px-3 py-2 border-b border-[#24242A]">
                      <div className="font-semibold text-white truncate">{user.name || "Entrepreneur"}</div>
                      <div className="text-[11px] text-zinc-400 truncate">{user.email}</div>
                      <div className="mt-1 inline-flex items-center gap-1 text-[10px] text-amber-400 font-mono bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                        <Shield className="w-2.5 h-2.5" />
                        <span>Google Verified</span>
                      </div>
                    </div>

                    <Link
                      href="/roadmap"
                      onClick={() => setUserDropdownOpen(false)}
                      className="flex items-center gap-2 px-3 py-2 text-zinc-300 hover:text-white hover:bg-zinc-900 transition-colors"
                    >
                      <span>My Startup Roadmap</span>
                    </Link>

                    <Link
                      href="/chat"
                      onClick={() => setUserDropdownOpen(false)}
                      className="flex items-center gap-2 px-3 py-2 text-zinc-300 hover:text-white hover:bg-zinc-900 transition-colors"
                    >
                      <span>AI Advisory Session</span>
                    </Link>

                    <button
                      onClick={() => {
                        setUserDropdownOpen(false);
                        logout();
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 border-t border-[#24242A] transition-colors"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={loginWithGoogle}
                disabled={isLoading}
                className="inline-flex items-center gap-2 bg-[#17171A] hover:bg-[#202026] border border-[#2F2F38] hover:border-amber-500/50 text-xs font-medium text-zinc-200 hover:text-white px-3 py-1.5 rounded-md shadow-sm transition-all group"
                title="Sign in with your Google account"
              >
                {isLoading ? (
                  <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />
                ) : (
                  <svg className="w-3.5 h-3.5 shrink-0" viewBox="0 0 24 24">
                    <path
                      fill="#EA4335"
                      d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.4l3.7 2.9C6.5 7.4 9 5 12 5z"
                    />
                    <path
                      fill="#4285F4"
                      d="M23.5 12.3c0-.8-.1-1.7-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.6 14.7c-.2-.7-.4-1.5-.4-2.4s.2-1.6.4-2.4L1.9 7C.7 9.4 0 12 0 14.7s.7 5.3 1.9 7.7l3.7-2.9z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23.5c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2-6.4-4.8L1.9 17c1.8 3.8 5.6 6.5 10.1 6.5z"
                    />
                  </svg>
                )}
                <span>Sign In</span>
              </button>
            )}

            <Link
              href="/onboarding"
              className="inline-flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 text-black px-3.5 py-1.5 rounded-md text-xs font-semibold shadow-sm transition-all"
            >
              <span>{t.hero.primaryCta}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden items-center gap-2">
            {isAuthenticated && user && (
              <div className="w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold text-[10px]">
                {(user.name || user.email || "U").charAt(0).toUpperCase()}
              </div>
            )}
            <button
              onClick={toggleLanguage}
              className="flex items-center gap-1 px-2.5 py-1 rounded-md border border-[#2E2E36] bg-[#151518] text-xs font-medium text-zinc-300"
            >
              <Globe className="w-3 h-3 text-amber-400" />
              <span>{language === "en" ? "தமிழ்" : "EN"}</span>
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-md text-zinc-400 hover:text-white hover:bg-zinc-900"
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
          {isAuthenticated && user && (
            <div className="px-3 py-2 mb-2 bg-[#141418] rounded-lg border border-[#272730] text-xs">
              <div className="font-semibold text-white">{user.name || "Entrepreneur"}</div>
              <div className="text-zinc-400 text-[11px] truncate">{user.email}</div>
            </div>
          )}

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

          <div className="pt-2 space-y-2">
            {isAuthenticated ? (
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  logout();
                }}
                className="w-full flex items-center justify-center gap-2 bg-rose-500/10 border border-rose-500/20 text-rose-400 py-2 rounded-md text-xs font-medium"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            ) : (
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  loginWithGoogle();
                }}
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 bg-[#1A1A20] border border-[#2E2E38] text-white py-2 rounded-md text-xs font-medium"
              >
                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24">
                  <path
                    fill="#EA4335"
                    d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.4l3.7 2.9C6.5 7.4 9 5 12 5z"
                  />
                  <path
                    fill="#4285F4"
                    d="M23.5 12.3c0-.8-.1-1.7-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.6 14.7c-.2-.7-.4-1.5-.4-2.4s.2-1.6.4-2.4L1.9 7C.7 9.4 0 12 0 14.7s.7 5.3 1.9 7.7l3.7-2.9z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23.5c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2-6.4-4.8L1.9 17c1.8 3.8 5.6 6.5 10.1 6.5z"
                  />
                </svg>
                <span>Sign in with Google</span>
              </button>
            )}

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

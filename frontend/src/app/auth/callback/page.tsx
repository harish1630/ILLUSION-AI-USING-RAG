"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { exchangeGoogleCode } from "@/lib/api";
import { Sparkles, Loader2, AlertCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";

function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuthSession } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState("Authenticating with Google...");

  useEffect(() => {
    async function handleAuth() {
      // 1. Check if backend redirected with ready JWT tokens
      const accessToken = searchParams.get("access_token");
      const refreshToken = searchParams.get("refresh_token");
      const userId = searchParams.get("user_id");
      const email = searchParams.get("email");

      if (accessToken && refreshToken) {
        setStatusMessage("Setting up your session...");
        setAuthSession(accessToken, refreshToken, {
          user_id: userId || "",
          email: email || "",
          roles: ["user"],
        });
        setTimeout(() => {
          router.replace("/");
        }, 500);
        return;
      }

      // 2. Check if authorization code was passed directly
      const code = searchParams.get("code");
      const urlError = searchParams.get("error");

      if (urlError) {
        setError(`Google Authentication was cancelled or failed: ${urlError}`);
        return;
      }

      if (code) {
        setStatusMessage("Exchanging Google authorization code...");
        try {
          const res = await exchangeGoogleCode(code);
          if (res?.tokens?.access_token) {
            setAuthSession(res.tokens.access_token, res.tokens.refresh_token, {
              user_id: res.user?.google_id || "",
              email: res.user?.email || "",
              name: res.user?.name || "",
              picture: res.user?.picture,
              roles: ["user"],
            });
            setTimeout(() => {
              router.replace("/");
            }, 500);
          } else {
            setError("No valid session tokens received from authentication server.");
          }
        } catch (err: any) {
          console.error("Code exchange failed:", err);
          setError(err.message || "Failed to exchange authorization code.");
        }
        return;
      }

      // If no code and no tokens
      setError("No authorization credentials found in callback URL.");
    }

    handleAuth();
  }, [searchParams, router, setAuthSession]);

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-[#121214] border border-[#24242A] rounded-2xl p-8 text-center shadow-2xl">
        <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 mx-auto mb-6">
          <Sparkles className="w-6 h-6" />
        </div>

        {error ? (
          <div>
            <div className="flex items-center justify-center gap-2 text-rose-400 font-semibold mb-3">
              <AlertCircle className="w-5 h-5" />
              <span>Authentication Error</span>
            </div>
            <p className="text-sm text-zinc-400 mb-6 bg-rose-500/10 border border-rose-500/20 p-3 rounded-lg font-mono text-xs">
              {error}
            </p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 bg-[#1A1A1E] hover:bg-[#25252B] border border-[#2E2E36] text-zinc-200 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Home</span>
            </Link>
          </div>
        ) : (
          <div>
            <h2 className="text-lg font-bold text-white mb-2">Connecting to illusion AI</h2>
            <p className="text-xs text-zinc-400 mb-6">{statusMessage}</p>
            <div className="flex items-center justify-center gap-2 text-amber-400 text-xs font-mono">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Please wait a moment</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[80vh] flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-amber-400 animate-spin" />
        </div>
      }
    >
      <CallbackHandler />
    </Suspense>
  );
}

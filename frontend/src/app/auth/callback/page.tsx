"use client";

import React, { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Loader2, Sparkles } from "lucide-react";

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuthSession } = useAuth();

  useEffect(() => {
    const error = searchParams.get("error");
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const authSuccess = searchParams.get("auth_success");

    if (error) {
      router.push(`/login?error=${encodeURIComponent(error)}`);
      return;
    }

    if (code && state) {
      // Forward to backend canonical exchange callback
      window.location.href = `/api/v1/auth/google/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`;
      return;
    }

    // Backend set cookies and redirected with auth_success
    router.push("/chat");
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-[#0D0D0E] flex flex-col items-center justify-center p-4">
      <div className="flex flex-col items-center gap-4 text-center">
        <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 animate-pulse">
          <Sparkles className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-base font-bold text-white mb-1">Authenticating with Illusion AI</h2>
          <p className="text-xs text-zinc-400">Verifying security token and initializing workspace...</p>
        </div>
        <Loader2 className="w-5 h-5 text-amber-400 animate-spin mt-2" />
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#0D0D0E] flex items-center justify-center text-zinc-400 text-xs">Loading...</div>}>
      <AuthCallbackContent />
    </Suspense>
  );
}

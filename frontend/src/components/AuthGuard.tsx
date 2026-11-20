"use client";

import React from "react";
import { useAuth } from "@/context/AuthContext";
import LoginGateway from "@/components/LoginGateway";
import { Loader2 } from "lucide-react";

interface AuthGuardProps {
  children: React.ReactNode;
}

export default function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
          <Loader2 className="w-5 h-5 animate-spin" />
        </div>
        <span className="text-xs font-mono text-zinc-400">Loading session...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginGateway />;
  }

  return <>{children}</>;
}

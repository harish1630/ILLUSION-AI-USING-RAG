"use client";

import React from "react";

interface AuthGuardProps {
  children: React.ReactNode;
}

/**
 * Clean passthrough AuthGuard with authentication gates removed.
 */
export default function AuthGuard({ children }: AuthGuardProps) {
  return <>{children}</>;
}

"use client";

import React, { createContext, useContext, ReactNode } from "react";

export interface UserProfile {
  user_id: string;
  email: string;
  name?: string;
  picture?: string;
  roles: string[];
}

interface AuthContextType {
  user: UserProfile;
  accessToken: string;
  isLoading: boolean;
  isAuthenticated: boolean;
  loginWithGoogle: () => Promise<void>;
  loginWithCredentials: (username_or_email: string, password: string) => Promise<void>;
  registerWithCredentials: (email: string, username: string, password: string, full_name?: string) => Promise<void>;
  sendForgotPassword: (email: string) => Promise<string | null>;
  performResetPassword: (token: string, new_password: string) => Promise<void>;
  loginAsGuest: () => void;
  logout: () => Promise<void>;
  setAuthSession: (accessToken: string, refreshToken: string, user?: UserProfile) => void;
}

const DEFAULT_USER: UserProfile = {
  user_id: "default_user",
  email: "founder@illusion.ai",
  name: "Entrepreneur",
  roles: ["user", "founder"],
};

const AuthContext = createContext<AuthContextType>({
  user: DEFAULT_USER,
  accessToken: "default_session_token",
  isLoading: false,
  isAuthenticated: true,
  loginWithGoogle: async () => {},
  loginWithCredentials: async () => {},
  registerWithCredentials: async () => {},
  sendForgotPassword: async () => null,
  performResetPassword: async () => {},
  loginAsGuest: () => {},
  logout: async () => {},
  setAuthSession: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  return (
    <AuthContext.Provider
      value={{
        user: DEFAULT_USER,
        accessToken: "default_session_token",
        isLoading: false,
        isAuthenticated: true,
        loginWithGoogle: async () => {},
        loginWithCredentials: async () => {},
        registerWithCredentials: async () => {},
        sendForgotPassword: async () => null,
        performResetPassword: async () => {},
        loginAsGuest: () => {},
        logout: async () => {},
        setAuthSession: () => {},
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import {
  getCurrentUser,
  loginWithPassword,
  registerWithPassword,
  logoutUser,
  getGoogleAuthUrl,
  forgotPassword,
  resetPassword,
} from "@/lib/api";

export interface UserProfile {
  user_id: string;
  email: string;
  username?: string;
  name?: string;
  picture?: string;
  roles: string[];
  is_verified?: boolean;
}

interface AuthContextType {
  user: UserProfile | null;
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

const GUEST_USER: UserProfile = {
  user_id: "default_user",
  email: "founder@illusion.ai",
  username: "founder",
  name: "Entrepreneur Founder",
  roles: ["user", "founder"],
};

const AuthContext = createContext<AuthContextType>({
  user: GUEST_USER,
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
  const [user, setUser] = useState<UserProfile | null>(GUEST_USER);
  const [accessToken, setAccessToken] = useState<string>("default_session_token");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);

  // Restore session on app load
  useEffect(() => {
    let isMounted = true;

    async function checkAuth() {
      try {
        const storedToken = typeof window !== "undefined" ? localStorage.getItem("illusion_access_token") : null;
        if (storedToken) {
          setAccessToken(storedToken);
        }

        // Check active session on server (using HttpOnly cookies or bearer header)
        const profile = await getCurrentUser(storedToken || undefined);
        if (isMounted && profile) {
          setUser(profile);
          setIsAuthenticated(true);
          if (typeof window !== "undefined") {
            localStorage.setItem("illusion_user_id", profile.user_id);
          }
        }
      } catch (err) {
        // Fall back gracefully to guest explorer if unauthenticated
        if (isMounted) {
          const guestPref = typeof window !== "undefined" ? localStorage.getItem("illusion_guest_mode") : null;
          if (guestPref === "true" || !localStorage.getItem("illusion_access_token")) {
            setUser(GUEST_USER);
            setIsAuthenticated(true);
          } else {
            setUser(null);
            setIsAuthenticated(false);
          }
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    checkAuth();
    return () => {
      isMounted = false;
    };
  }, []);

  const loginWithGoogle = async () => {
    try {
      const data = await getGoogleAuthUrl();
      if (data?.auth_url) {
        window.location.href = data.auth_url;
      }
    } catch (err: any) {
      console.error("Google login failed to launch:", err);
      throw err;
    }
  };

  const loginWithCredentials = async (username_or_email: string, password: string) => {
    setIsLoading(true);
    try {
      const resp = await loginWithPassword({ username_or_email, password });
      if (resp?.tokens?.access_token) {
        setAuthSession(resp.tokens.access_token, resp.tokens.refresh_token, resp.user);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const registerWithCredentials = async (
    email: string,
    username: string,
    password: string,
    full_name?: string
  ) => {
    setIsLoading(true);
    try {
      const resp = await registerWithPassword({ email, username, password, full_name });
      if (resp?.tokens?.access_token) {
        setAuthSession(resp.tokens.access_token, resp.tokens.refresh_token, resp.user);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const setAuthSession = (access: string, refresh: string, profile?: UserProfile) => {
    setAccessToken(access);
    setIsAuthenticated(true);
    if (profile) setUser(profile);

    if (typeof window !== "undefined") {
      localStorage.setItem("illusion_access_token", access);
      localStorage.setItem("illusion_refresh_token", refresh);
      if (profile?.user_id) localStorage.setItem("illusion_user_id", profile.user_id);
    }
  };

  const sendForgotPassword = async (email: string): Promise<string | null> => {
    const res = await forgotPassword(email);
    return res?.debug_token || null;
  };

  const performResetPassword = async (token: string, new_password: string) => {
    await resetPassword({ token, new_password });
  };

  const loginAsGuest = () => {
    setUser(GUEST_USER);
    setAccessToken("default_session_token");
    setIsAuthenticated(true);
    if (typeof window !== "undefined") {
      localStorage.setItem("illusion_guest_mode", "true");
      localStorage.setItem("illusion_user_id", "default_user");
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await logoutUser(accessToken);
    } finally {
      setUser(null);
      setAccessToken("");
      setIsAuthenticated(false);
      if (typeof window !== "undefined") {
        localStorage.removeItem("illusion_access_token");
        localStorage.removeItem("illusion_refresh_token");
        localStorage.removeItem("illusion_user_id");
        localStorage.removeItem("illusion_guest_mode");
      }
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        isLoading,
        isAuthenticated,
        loginWithGoogle,
        loginWithCredentials,
        registerWithCredentials,
        sendForgotPassword,
        performResetPassword,
        loginAsGuest,
        logout,
        setAuthSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

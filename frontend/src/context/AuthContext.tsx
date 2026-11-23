"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import {
  getGoogleAuthUrl,
  getCurrentUser,
  logoutUser,
  refreshToken as refreshTokensApi,
  loginWithPassword as apiLoginWithPassword,
  registerWithPassword as apiRegisterWithPassword,
  forgotPassword as apiForgotPassword,
  resetPassword as apiResetPassword,
} from "@/lib/api";

export interface UserProfile {
  user_id: string;
  email: string;
  name?: string;
  picture?: string;
  roles: string[];
}

interface AuthContextType {
  user: UserProfile | null;
  accessToken: string | null;
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

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const ACCESS_TOKEN_KEY = "illusion_ai_access_token";
const REFRESH_TOKEN_KEY = "illusion_ai_refresh_token";
const USER_KEY = "illusion_ai_user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore session from localStorage on initial load
  useEffect(() => {
    async function restoreSession() {
      try {
        const storedAccess = localStorage.getItem(ACCESS_TOKEN_KEY);
        const storedRefresh = localStorage.getItem(REFRESH_TOKEN_KEY);
        const storedUser = localStorage.getItem(USER_KEY);

        if (storedUser) {
          try {
            setUser(JSON.parse(storedUser));
          } catch {
            // ignore JSON parse error
          }
        }

        if (storedAccess) {
          setAccessToken(storedAccess);
          if (storedAccess.startsWith("guest_")) {
            if (storedUser) {
              try {
                setUser(JSON.parse(storedUser));
              } catch {
                // ignore
              }
            } else {
              setUser({
                user_id: "guest_user",
                email: "guest@illusion.ai",
                name: "Guest Explorer",
                roles: ["guest"],
              });
            }
            setIsLoading(false);
            return;
          }

          // Verify with backend /auth/me
          try {
            const profile = await getCurrentUser(storedAccess);
            if (profile) {
              setUser(profile);
              localStorage.setItem(USER_KEY, JSON.stringify(profile));
            }
          } catch (err) {
            // Token might be expired, try refresh
            if (storedRefresh) {
              try {
                const refreshed = await refreshTokensApi(storedRefresh);
                if (refreshed?.access_token) {
                  setAccessToken(refreshed.access_token);
                  localStorage.setItem(ACCESS_TOKEN_KEY, refreshed.access_token);
                  if (refreshed.refresh_token) {
                    localStorage.setItem(REFRESH_TOKEN_KEY, refreshed.refresh_token);
                  }
                  const profile = await getCurrentUser(refreshed.access_token);
                  if (profile) {
                    setUser(profile);
                    localStorage.setItem(USER_KEY, JSON.stringify(profile));
                  }
                } else {
                  clearSession();
                }
              } catch {
                clearSession();
              }
            } else {
              clearSession();
            }
          }
        }
      } catch (err) {
        console.error("Failed to restore auth session:", err);
      } finally {
        setIsLoading(false);
      }
    }

    restoreSession();
  }, []);

  const clearSession = () => {
    setUser(null);
    setAccessToken(null);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  };

  const setAuthSession = (access: string, refresh: string, profile?: UserProfile) => {
    setAccessToken(access);
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);

    if (profile) {
      setUser(profile);
      localStorage.setItem(USER_KEY, JSON.stringify(profile));
    }
  };

  const loginWithGoogle = async () => {
    try {
      setIsLoading(true);
      const data = await getGoogleAuthUrl();
      if (data?.authorization_url) {
        window.location.href = data.authorization_url;
      } else {
        alert("Google OAuth is not configured yet on backend.");
      }
    } catch (err: any) {
      console.error("Login with Google failed:", err);
      alert("Could not initialize Google Sign-In. Please check backend connection.");
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithCredentials = async (username_or_email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await apiLoginWithPassword({ username_or_email, password });
      if (res?.tokens?.access_token) {
        setAuthSession(res.tokens.access_token, res.tokens.refresh_token, {
          user_id: res.user.id,
          email: res.user.email,
          name: res.user.full_name || res.user.username,
          picture: res.user.picture,
          roles: ["user"],
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const registerWithCredentials = async (email: string, username: string, password: string, full_name?: string) => {
    setIsLoading(true);
    try {
      const res = await apiRegisterWithPassword({ email, username, password, full_name });
      if (res?.tokens?.access_token) {
        setAuthSession(res.tokens.access_token, res.tokens.refresh_token, {
          user_id: res.user.id,
          email: res.user.email,
          name: res.user.full_name || res.user.username,
          picture: res.user.picture,
          roles: ["user"],
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const sendForgotPassword = async (email: string): Promise<string | null> => {
    const res = await apiForgotPassword(email);
    return res?.reset_token || null;
  };

  const performResetPassword = async (token: string, new_password: string) => {
    await apiResetPassword({ token, new_password });
  };

  const loginAsGuest = () => {
    const guestUser: UserProfile = {
      user_id: `guest_${Date.now()}`,
      email: "guest@illusion.ai",
      name: "Guest Entrepreneur",
      roles: ["guest"],
    };
    setAuthSession("guest_access_token", "guest_refresh_token", guestUser);
  };

  const logout = async () => {
    try {
      if (accessToken) {
        await logoutUser(accessToken);
      }
    } catch (err) {
      console.warn("Logout request failed on backend:", err);
    } finally {
      clearSession();
      window.location.href = "/";
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        isLoading,
        isAuthenticated: !!user && !!accessToken,
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
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

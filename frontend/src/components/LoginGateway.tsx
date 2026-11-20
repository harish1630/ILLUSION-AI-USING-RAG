"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import {
  Sparkles,
  Shield,
  ArrowRight,
  Globe,
  Loader2,
  CheckCircle2,
  Lock,
  Mail,
  User as UserIcon,
  KeyRound,
  Eye,
  EyeOff,
  AlertCircle,
  HelpCircle,
} from "lucide-react";

type AuthMode = "signin" | "signup" | "forgot" | "reset";

export default function LoginGateway() {
  const {
    isAuthenticated,
    isLoading: authLoading,
    loginWithGoogle,
    loginWithCredentials,
    registerWithCredentials,
    sendForgotPassword,
    performResetPassword,
    loginAsGuest,
  } = useAuth();
  const { language, toggleLanguage } = useLanguage();
  const router = useRouter();

  // Component UI State
  const [mode, setMode] = useState<AuthMode>("signin");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form Fields
  const [identifier, setIdentifier] = useState(""); // username or email
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, router]);

  const isTamil = language === "ta";

  // Reset errors when mode changes
  const switchMode = (newMode: AuthMode) => {
    setMode(newMode);
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  // 1. Handle Sign In
  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!identifier.trim() || !password) {
      setErrorMessage(isTamil ? "பயனர்பெயர்/மின்னஞ்சல் மற்றும் கடவுச்சொல்லை உள்ளிடவும்." : "Please enter your username/email and password.");
      return;
    }

    setSubmitting(true);
    try {
      await loginWithCredentials(identifier.trim(), password);
      router.push("/");
    } catch (err: any) {
      setErrorMessage(err.message || (isTamil ? "உள்நுழைவு தோல்வியடைந்தது. விவரங்களை சரிபார்க்கவும்." : "Sign in failed. Please check your credentials."));
    } finally {
      setSubmitting(false);
    }
  };

  // 2. Handle Sign Up
  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!email.trim() || !username.trim() || !password) {
      setErrorMessage(isTamil ? "அனைத்து புலங்களையும் நிரப்பவும்." : "Please fill in all required fields.");
      return;
    }

    if (password.length < 6) {
      setErrorMessage(isTamil ? "கடவுச்சொல் குறைந்தது 6 எழுத்துகள் கொண்டிருக்க வேண்டும்." : "Password must be at least 6 characters.");
      return;
    }

    setSubmitting(true);
    try {
      await registerWithCredentials(email.trim(), username.trim(), password, fullName.trim() || undefined);
      setSuccessMessage(isTamil ? "கணக்கு வெற்றிகரமாக உருவாக்கப்பட்டது! வழிநடத்துகிறது..." : "Account created successfully! Redirecting...");
      setTimeout(() => {
        router.push("/");
      }, 500);
    } catch (err: any) {
      setErrorMessage(err.message || (isTamil ? "பதிவு தோல்வியடைந்தது." : "Registration failed."));
    } finally {
      setSubmitting(false);
    }
  };

  // 3. Handle Forgot Password
  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!email.trim()) {
      setErrorMessage(isTamil ? "உங்கள் பதிவு செய்யப்பட்ட மின்னஞ்சலை உள்ளிடவும்." : "Please enter your registered email address.");
      return;
    }

    setSubmitting(true);
    try {
      const generatedToken = await sendForgotPassword(email.trim());
      if (generatedToken) {
        setResetToken(generatedToken);
        setMode("reset");
        setSuccessMessage(
          isTamil
            ? "கடவுச்சொல் மீட்டமைப்பு குறியீடு உருவாக்கப்பட்டது. புதிய கடவுச்சொல்லை உள்ளிடவும்."
            : "Password reset token generated! Please set your new password below."
        );
      } else {
        setSuccessMessage(
          isTamil
            ? "மின்னஞ்சல் பதிவு செய்யப்பட்டிருந்தால், வழிமுறைகள் அனுப்பப்பட்டுள்ளன."
            : "If this email is registered, instructions have been prepared."
        );
      }
    } catch (err: any) {
      setErrorMessage(err.message || (isTamil ? "மீட்டமைக்க முடியவில்லை." : "Failed to initiate password reset."));
    } finally {
      setSubmitting(false);
    }
  };

  // 4. Handle Reset Password
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!resetToken.trim() || !newPassword) {
      setErrorMessage(isTamil ? "குறியீடு மற்றும் புதிய கடவுச்சொல்லை உள்ளிடவும்." : "Please provide reset token and new password.");
      return;
    }

    if (newPassword.length < 6) {
      setErrorMessage(isTamil ? "கடவுச்சொல் குறைந்தது 6 எழுத்துகள் கொண்டிருக்க வேண்டும்." : "Password must be at least 6 characters.");
      return;
    }

    setSubmitting(true);
    try {
      await performResetPassword(resetToken.trim(), newPassword);
      setSuccessMessage(
        isTamil
          ? "கடவுச்சொல் வெற்றிகரமாக மாற்றப்பட்டது! இப்போது உள்நுழையலாம்."
          : "Password updated successfully! You can now sign in with your new password."
      );
      setPassword("");
      setMode("signin");
    } catch (err: any) {
      setErrorMessage(err.message || (isTamil ? "கடவுச்சொல்லை மீட்டமைக்க முடியவில்லை." : "Failed to reset password. Invalid or expired token."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0A0C] flex flex-col justify-between text-zinc-100 relative overflow-hidden selection:bg-amber-500/20 selection:text-amber-300">
      {/* Background Ambient Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-gradient-to-b from-amber-500/10 via-amber-500/5 to-transparent blur-3xl pointer-events-none -z-0" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[300px] bg-amber-500/5 blur-3xl pointer-events-none -z-0" />

      {/* Top Header bar with Language switcher */}
      <header className="relative z-10 max-w-6xl mx-auto w-full px-6 py-6 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#141417] border border-[#26262E] flex items-center justify-center text-amber-400 shadow-sm">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <span className="text-base font-bold tracking-tight text-white font-sans flex items-center gap-1.5">
              illusion <span className="text-amber-400 font-extrabold">AI</span>
            </span>
          </div>
        </div>

        <button
          onClick={toggleLanguage}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#2B2B33] bg-[#141417] text-xs font-medium text-zinc-300 hover:text-white hover:border-zinc-500 transition-colors"
        >
          <Globe className="w-3.5 h-3.5 text-amber-400" />
          <span>{isTamil ? "English" : "தமிழ் (Tamil)"}</span>
        </button>
      </header>

      {/* Main Login / Registration Card */}
      <main className="relative z-10 flex-1 flex items-center justify-center px-4 py-6">
        <div className="max-w-md w-full bg-[#121215]/95 border border-[#24242B] rounded-3xl p-7 sm:p-9 shadow-2xl backdrop-blur-xl">
          {/* Header Title */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/25 text-amber-400 text-xs font-mono mb-3">
              <Lock className="w-3 h-3" />
              <span>
                {mode === "signin" && (isTamil ? "உள்நுழைவு" : "Secure Sign In")}
                {mode === "signup" && (isTamil ? "புதிய கணக்கு" : "Create Account")}
                {mode === "forgot" && (isTamil ? "கடவுச்சொல் மீட்பு" : "Forgot Password")}
                {mode === "reset" && (isTamil ? "புதிய கடவுச்சொல்" : "Reset Password")}
              </span>
            </div>

            <h1 className="text-2xl font-extrabold tracking-tight text-white mb-1">
              {mode === "signin" && (isTamil ? "மீண்டும் வருக" : "Welcome Back")}
              {mode === "signup" && (isTamil ? "பதிவு செய்க" : "Get Started with illusion AI")}
              {mode === "forgot" && (isTamil ? "கடவுச்சொல் மீட்பு" : "Reset Your Password")}
              {mode === "reset" && (isTamil ? "புதிய கடவுச்சொல்லை அமைக்குக" : "Set New Password")}
            </h1>
            <p className="text-xs text-zinc-400">
              {mode === "signin" && (isTamil ? "உங்கள் பயனர்பெயர் அல்லது மின்னஞ்சல் மூலம் தொடரவும்" : "Enter your username or email address and password")}
              {mode === "signup" && (isTamil ? "அரசு மானியங்கள் & AI வழிகாட்டியை அணுக கணக்கு தொடங்குக" : "Sign up with your email, username, and password")}
              {mode === "forgot" && (isTamil ? "மீட்டமைப்பு குறியீட்டைப் பெற உங்கள் மின்னஞ்சலை உள்ளிடவும்" : "Enter your email to receive a password reset token")}
              {mode === "reset" && (isTamil ? "குறியீடு மற்றும் உங்கள் புதிய கடவுச்சொல்லை உள்ளிடவும்" : "Enter the token and your new secure password")}
            </p>
          </div>

          {/* Mode Switch Tabs (Sign In / Sign Up) */}
          {(mode === "signin" || mode === "signup") && (
            <div className="flex rounded-xl bg-[#17171C] p-1 border border-[#26262E] mb-6 text-xs">
              <button
                type="button"
                onClick={() => switchMode("signin")}
                className={`flex-1 py-2 rounded-lg font-medium transition-all ${
                  mode === "signin"
                    ? "bg-[#25252D] text-amber-400 font-semibold shadow-sm"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                {isTamil ? "உள்நுழைக (Sign In)" : "Sign In"}
              </button>
              <button
                type="button"
                onClick={() => switchMode("signup")}
                className={`flex-1 py-2 rounded-lg font-medium transition-all ${
                  mode === "signup"
                    ? "bg-[#25252D] text-amber-400 font-semibold shadow-sm"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                {isTamil ? "பதிவு செய்க (Sign Up)" : "Sign Up"}
              </button>
            </div>
          )}

          {/* Feedback Banners */}
          {errorMessage && (
            <div className="mb-4 flex items-start gap-2 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div className="mb-4 flex items-start gap-2 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-300 text-xs">
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* MODE 1: SIGN IN FORM */}
          {mode === "signin" && (
            <form onSubmit={handleSignIn} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1.5">
                  {isTamil ? "பயனர்பெயர் அல்லது மின்னஞ்சல் (Username / Email)" : "Username or Email ID"}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                    <UserIcon className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    required
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    placeholder={isTamil ? "எ.கா. arun அல்லது arun@example.com" : "e.g. founder or founder@example.com"}
                    className="w-full bg-[#18181D] border border-[#2B2B33] focus:border-amber-500 focus:ring-1 focus:ring-amber-500 rounded-xl pl-9 pr-3 py-2.5 text-xs text-white placeholder-zinc-500 transition-colors"
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-xs font-medium text-zinc-300">
                    {isTamil ? "கடவுச்சொல் (Password)" : "Password"}
                  </label>
                  <button
                    type="button"
                    onClick={() => switchMode("forgot")}
                    className="text-[11px] text-amber-400 hover:text-amber-300 transition-colors"
                  >
                    {isTamil ? "கடவுச்சொல் மறந்ததா?" : "Forgot password?"}
                  </button>
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                    <KeyRound className="w-4 h-4" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-[#18181D] border border-[#2B2B33] focus:border-amber-500 focus:ring-1 focus:ring-amber-500 rounded-xl pl-9 pr-10 py-2.5 text-xs text-white placeholder-zinc-500 transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-zinc-500 hover:text-zinc-300"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full mt-2 flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-black py-2.5 px-4 rounded-xl font-semibold text-xs shadow-md transition-all disabled:opacity-50"
              >
                {submitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <span>{isTamil ? "உள்நுழைக" : "Sign In"}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </form>
          )}

          {/* MODE 2: SIGN UP FORM */}
          {mode === "signup" && (
            <form onSubmit={handleSignUp} className="space-y-3.5">
              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">
                  {isTamil ? "மின்னஞ்சல் முகவரி (Email ID)" : "Email Address"}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="founder@example.com"
                    className="w-full bg-[#18181D] border border-[#2B2B33] focus:border-amber-500 focus:ring-1 focus:ring-amber-500 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-zinc-500 transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">
                  {isTamil ? "பயனர்பெயர் (Username)" : "Username"}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                    <UserIcon className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="founder_tn"
                    className="w-full bg-[#18181D] border border-[#2B2B33] focus:border-amber-500 focus:ring-1 focus:ring-amber-500 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-zinc-500 transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">
                  {isTamil ? "முழு பெயர் (Full Name - விருப்பத்திற்குரியது)" : "Full Name (Optional)"}
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Karthik Raja"
                  className="w-full bg-[#18181D] border border-[#2B2B33] focus:border-amber-500 focus:ring-1 focus:ring-amber-500 rounded-xl px-3 py-2 text-xs text-white placeholder-zinc-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">
                  {isTamil ? "கடவுச்சொல் (Password - குறைந்தது 6 எழுத்துகள்)" : "Password (min 6 characters)"}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                    <KeyRound className="w-4 h-4" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    minLength={6}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-[#18181D] border border-[#2B2B33] focus:border-amber-500 focus:ring-1 focus:ring-amber-500 rounded-xl pl-9 pr-10 py-2 text-xs text-white placeholder-zinc-500 transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-zinc-500 hover:text-zinc-300"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full mt-2 flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-black py-2.5 px-4 rounded-xl font-semibold text-xs shadow-md transition-all disabled:opacity-50"
              >
                {submitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <span>{isTamil ? "கணக்கு தொடங்குக" : "Create Account"}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </form>
          )}

          {/* MODE 3: FORGOT PASSWORD */}
          {mode === "forgot" && (
            <form onSubmit={handleForgotPassword} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1.5">
                  {isTamil ? "பதிவு செய்யப்பட்ட மின்னஞ்சல் முகவரி" : "Your Registered Email ID"}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="founder@example.com"
                    className="w-full bg-[#18181D] border border-[#2B2B33] focus:border-amber-500 focus:ring-1 focus:ring-amber-500 rounded-xl pl-9 pr-3 py-2.5 text-xs text-white placeholder-zinc-500 transition-colors"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-black py-2.5 px-4 rounded-xl font-semibold text-xs shadow-md transition-all disabled:opacity-50"
              >
                {submitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <span>{isTamil ? "மீட்டமைப்பு குறியீடு பெறுக" : "Generate Reset Token"}</span>
                )}
              </button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => switchMode("signin")}
                  className="text-xs text-zinc-400 hover:text-white transition-colors"
                >
                  ← {isTamil ? "உள்நுழைவிற்கு திரும்புக" : "Back to Sign In"}
                </button>
              </div>
            </form>
          )}

          {/* MODE 4: RESET PASSWORD */}
          {mode === "reset" && (
            <form onSubmit={handleResetPassword} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">
                  {isTamil ? "மீட்டமைப்பு குறியீடு (Reset Token)" : "Password Reset Token"}
                </label>
                <input
                  type="text"
                  required
                  value={resetToken}
                  onChange={(e) => setResetToken(e.target.value)}
                  placeholder="Paste reset token"
                  className="w-full bg-[#18181D] border border-[#2B2B33] focus:border-amber-500 focus:ring-1 focus:ring-amber-500 rounded-xl px-3 py-2.5 text-xs text-white font-mono placeholder-zinc-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">
                  {isTamil ? "புதிய கடவுச்சொல் (New Password)" : "New Password (min 6 characters)"}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                    <KeyRound className="w-4 h-4" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    minLength={6}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-[#18181D] border border-[#2B2B33] focus:border-amber-500 focus:ring-1 focus:ring-amber-500 rounded-xl pl-9 pr-10 py-2.5 text-xs text-white placeholder-zinc-500 transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-zinc-500 hover:text-zinc-300"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-black py-2.5 px-4 rounded-xl font-semibold text-xs shadow-md transition-all disabled:opacity-50"
              >
                {submitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <span>{isTamil ? "கடவுச்சொல்லை மாற்றுக" : "Update Password"}</span>
                )}
              </button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => switchMode("signin")}
                  className="text-xs text-zinc-400 hover:text-white transition-colors"
                >
                  ← {isTamil ? "உள்நுழைவிற்கு திரும்புக" : "Back to Sign In"}
                </button>
              </div>
            </form>
          )}

          {/* Social Divider (for Sign In & Sign Up) */}
          {(mode === "signin" || mode === "signup") && (
            <>
              <div className="relative my-6 text-center">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-[#26262E]" />
                </div>
                <span className="relative bg-[#121215] px-3 text-[11px] uppercase tracking-wider text-zinc-500 font-mono">
                  {isTamil ? "அல்லது" : "or continue with"}
                </span>
              </div>

              {/* Google OAuth Button */}
              <button
                type="button"
                onClick={loginWithGoogle}
                disabled={authLoading}
                className="w-full flex items-center justify-center gap-3 bg-[#18181D] hover:bg-[#202026] text-white py-2.5 px-4 rounded-xl border border-[#2E2E38] hover:border-amber-500/50 font-medium text-xs transition-all duration-200 shadow-sm group disabled:opacity-50"
              >
                {authLoading ? (
                  <Loader2 className="w-4 h-4 text-amber-400 animate-spin" />
                ) : (
                  <svg className="w-4 h-4 shrink-0 transition-transform group-hover:scale-110" viewBox="0 0 24 24">
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
                <span>{isTamil ? "கூகிள் மூலம் உள்நுழைக" : "Sign In with Google"}</span>
              </button>

              {/* Guest Exploration Option */}
              <div className="mt-4 text-center">
                <button
                  type="button"
                  onClick={() => {
                    loginAsGuest();
                    router.push("/");
                  }}
                  className="text-[11px] text-zinc-400 hover:text-amber-400 font-mono transition-colors"
                >
                  {isTamil ? "விருந்தினராக தொடரவும் (டெமோ) →" : "Continue as Guest Explorer →"}
                </button>
              </div>
            </>
          )}
        </div>
      </main>

      {/* Subtle footer */}
      <footer className="relative z-10 max-w-6xl mx-auto w-full px-6 py-4 text-center text-[11px] text-zinc-500 font-mono">
        illusion AI — Guiding first-time entrepreneurs through startup & government schemes.
      </footer>
    </div>
  );
}

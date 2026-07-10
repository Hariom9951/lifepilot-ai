"use client";

import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Brain, Lock, Mail, User, Eye, EyeOff, Loader2 } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { apiClient } from "@/config/axios";
import { useToast } from "@/components/ui/toast";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const loginSchema = z.object({
  username_or_email: z.string().min(1, "Username or Email is required"),
  password: z.string().min(1, "Password is required"),
});

type LoginFields = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const { setSession, isAuthenticated } = useAuthStore();

  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const redirectPath = searchParams.get("redirect") || "/";

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      router.push(redirectPath);
    }
  }, [isAuthenticated, redirectPath, router]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFields>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFields) => {
    setSubmitting(true);
    try {
      const response = await apiClient.post("/auth/login", data);
      const { access_token, user } = response.data.data;
      
      setSession(access_token, user);
      toast("Welcome back! Authentication successful.", "success");
      
      router.push(redirectPath);
    } catch (error: any) {
      const msg = error.response?.data?.message || "Invalid credentials, please try again.";
      toast(msg, "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 font-sans flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      {/* Dynamic abstract grid background */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />
      
      <Card className="max-w-md w-full p-8 relative border border-slate-200/50 bg-white/60 dark:border-slate-850 dark:bg-slate-900/40 backdrop-blur-xl shadow-2xl rounded-3xl">
        <div className="flex flex-col items-center mb-8">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/20 mb-4 animate-pulse">
            <Brain className="h-6 w-6 text-white" />
          </div>
          <h2 className="text-xl font-black tracking-tight text-slate-900 dark:text-white">
            Welcome to LifePilot <span className="text-indigo-500">AI</span>
          </h2>
          <p className="text-[10px] text-slate-450 dark:text-slate-500 mt-1 uppercase tracking-wider font-mono">
            Secure Console Access
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <div className="space-y-4">
            <div className="relative">
              <Input
                label="Username or Email Address"
                type="text"
                {...register("username_or_email")}
                placeholder="alex@lifepilot.ai"
                required
              />
              {errors.username_or_email && (
                <p className="text-[10px] text-rose-500 font-semibold mt-1">
                  {errors.username_or_email.message}
                </p>
              )}
            </div>

            <div className="relative">
              <div className="relative">
                <Input
                  label="Password"
                  type={showPassword ? "text" : "password"}
                  {...register("password")}
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-[32px] text-slate-450 hover:text-slate-700 dark:hover:text-slate-200 focus:outline-none cursor-pointer"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-[10px] text-rose-500 font-semibold mt-1">
                  {errors.password.message}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-450 dark:text-slate-500">
            <div className="flex items-center gap-1.5">
              <input
                id="remember_me"
                type="checkbox"
                className="h-3.5 w-3.5 rounded border-slate-200 text-indigo-600 focus:ring-indigo-500 dark:border-slate-800"
              />
              <label htmlFor="remember_me" className="cursor-pointer">
                Remember session
              </label>
            </div>
            <Link
              href="/forgot-password"
              className="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 font-bold transition-colors"
            >
              Forgot Password?
            </Link>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full flex justify-center items-center py-2.5 px-4 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-500/10 hover:shadow-indigo-500/20 cursor-pointer focus:outline-none disabled:opacity-50 transition-all gap-2"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Signing In...
              </>
            ) : (
              "Sign In to Console"
            )}
          </button>
        </form>

        <div className="mt-6 text-center text-[11px] text-slate-450 dark:text-slate-500">
          New to the cockpit?{" "}
          <Link
            href="/register"
            className="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 font-bold transition-colors"
          >
            Create an Account
          </Link>
        </div>
      </Card>
    </div>
  );
}

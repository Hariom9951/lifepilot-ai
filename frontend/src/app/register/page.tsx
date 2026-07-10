"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Brain, Lock, Mail, User, Eye, EyeOff, Loader2, Globe, Clock } from "lucide-react";

import { apiClient } from "@/config/axios";
import { useToast } from "@/components/ui/toast";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const registerSchema = z
  .object({
    full_name: z.string().min(1, "Full Name is required").max(100),
    username: z
      .string()
      .min(3, "Username must be at least 3 characters")
      .max(50)
      .regex(/^[a-zA-Z0-9_-]+$/, "Can only contain letters, numbers, underscores, and hyphens"),
    email: z.string().email("Invalid email address").max(255),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Must contain at least one uppercase letter")
      .regex(/[a-z]/, "Must contain at least one lowercase letter")
      .regex(/[0-9]/, "Must contain at least one number")
      .regex(/[^a-zA-Z0-9]/, "Must contain at least one special character"),
    confirm_password: z.string().min(1, "Please confirm your password"),
    timezone: z.string().min(1, "Timezone is required"),
    language: z.string().min(1, "Language is required"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type RegisterFields = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { toast } = useToast();

  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFields>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      timezone: "UTC",
      language: "en",
    },
  });

  const onSubmit = async (data: RegisterFields) => {
    setSubmitting(true);
    try {
      // Remove confirm_password before sending to API
      const { confirm_password, ...payload } = data;
      await apiClient.post("/auth/register", payload);
      
      toast("Account created successfully! Please sign in.", "success");
      router.push("/login");
    } catch (error: any) {
      const msg = error.response?.data?.message || "Registration failed, please try again.";
      toast(msg, "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 font-sans flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />
      
      <Card className="max-w-md w-full p-8 relative border border-slate-200/50 bg-white/60 dark:border-slate-850 dark:bg-slate-900/40 backdrop-blur-xl shadow-2xl rounded-3xl">
        <div className="flex flex-col items-center mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/20 mb-4 animate-pulse">
            <Brain className="h-6 w-6 text-white" />
          </div>
          <h2 className="text-xl font-black tracking-tight text-slate-900 dark:text-white">
            Create LifePilot Account
          </h2>
          <p className="text-[10px] text-slate-450 dark:text-slate-500 mt-1 uppercase tracking-wider font-mono">
            Provision New Private Container
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-3">
            <div>
              <Input
                label="Full Name"
                type="text"
                {...register("full_name")}
                placeholder="Alex Mercer"
                required
              />
              {errors.full_name && (
                <p className="text-[10px] text-rose-500 font-semibold mt-1">
                  {errors.full_name.message}
                </p>
              )}
            </div>

            <div>
              <Input
                label="Username"
                type="text"
                {...register("username")}
                placeholder="alexmercer"
                required
              />
              {errors.username && (
                <p className="text-[10px] text-rose-500 font-semibold mt-1">
                  {errors.username.message}
                </p>
              )}
            </div>

            <div>
              <Input
                label="Email Address"
                type="email"
                {...register("email")}
                placeholder="alex@lifepilot.ai"
                required
              />
              {errors.email && (
                <p className="text-[10px] text-rose-500 font-semibold mt-1">
                  {errors.email.message}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-1.5 flex items-center gap-1">
                  <Clock className="h-3 w-3" /> Timezone
                </label>
                <select
                  {...register("timezone")}
                  className="w-full text-xs px-3 py-2 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-800 dark:text-slate-200 outline-none focus:border-indigo-500"
                >
                  <option value="UTC">UTC (Greenwich)</option>
                  <option value="America/New_York">EST (New York)</option>
                  <option value="America/Los_Angeles">PST (Los Angeles)</option>
                  <option value="Europe/London">GMT (London)</option>
                  <option value="Europe/Paris">CET (Paris)</option>
                  <option value="Asia/Tokyo">JST (Tokyo)</option>
                  <option value="Asia/Kolkata">IST (Kolkata)</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-1.5 flex items-center gap-1">
                  <Globe className="h-3 w-3" /> Language
                </label>
                <select
                  {...register("language")}
                  className="w-full text-xs px-3 py-2 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-800 dark:text-slate-200 outline-none focus:border-indigo-500"
                >
                  <option value="en">English</option>
                  <option value="es">Español</option>
                  <option value="de">Deutsch</option>
                  <option value="fr">Français</option>
                </select>
              </div>
            </div>

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
              {errors.password && (
                <p className="text-[10px] text-rose-500 font-semibold mt-1">
                  {errors.password.message}
                </p>
              )}
            </div>

            <div>
              <Input
                label="Confirm Password"
                type={showPassword ? "text" : "password"}
                {...register("confirm_password")}
                placeholder="••••••••"
                required
              />
              {errors.confirm_password && (
                <p className="text-[10px] text-rose-500 font-semibold mt-1">
                  {errors.confirm_password.message}
                </p>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full flex justify-center items-center py-2.5 px-4 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-500/10 hover:shadow-indigo-500/20 cursor-pointer focus:outline-none disabled:opacity-50 transition-all gap-2 mt-2"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Creating Cabin...
              </>
            ) : (
              "Initialize Cockpit Account"
            )}
          </button>
        </form>

        <div className="mt-5 text-center text-[11px] text-slate-450 dark:text-slate-500">
          Already have a cabin?{" "}
          <Link
            href="/login"
            className="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 font-bold transition-colors"
          >
            Sign In
          </Link>
        </div>
      </Card>
    </div>
  );
}

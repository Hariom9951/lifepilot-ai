"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { Brain, Mail, Loader2, ArrowLeft, CheckCircle2 } from "lucide-react";

import { useToast } from "@/components/ui/toast";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const forgotPasswordSchema = z.object({
  email: z.string().email("Invalid email address").max(255),
});

type ForgotPasswordFields = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordPage() {
  const { toast } = useToast();
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFields>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordFields) => {
    setSubmitting(true);
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setSubmitting(false);
    setSuccess(true);
    toast("Reset link sent! Please check your inbox.", "success");
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 font-sans flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />
      
      <Card className="max-w-md w-full p-8 relative border border-slate-200/50 bg-white/60 dark:border-slate-850 dark:bg-slate-900/40 backdrop-blur-xl shadow-2xl rounded-3xl animate-fade-in">
        <div className="flex flex-col items-center mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/20 mb-4 animate-pulse">
            <Brain className="h-6 w-6 text-white" />
          </div>
          <h2 className="text-xl font-black tracking-tight text-slate-900 dark:text-white">
            Reset Password
          </h2>
          <p className="text-[10px] text-slate-450 dark:text-slate-500 mt-1 uppercase tracking-wider font-mono">
            Recover cockpit key
          </p>
        </div>

        {success ? (
          <div className="space-y-6 text-center animate-fade-in">
            <div className="flex justify-center">
              <CheckCircle2 className="h-14 w-14 text-emerald-500" />
            </div>
            <div className="space-y-2">
              <h3 className="text-sm font-bold text-slate-850 dark:text-white">
                Transmission Dispatched
              </h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 max-w-xs mx-auto leading-relaxed">
                We have sent instructions to your email address if a registered account exists. Please check your inbox and spam folders.
              </p>
            </div>
            <Link
              href="/login"
              className="w-full flex justify-center items-center py-2.5 px-4 rounded-xl text-xs font-bold bg-slate-200 hover:bg-slate-350 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 cursor-pointer focus:outline-none transition-all gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Return to login
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <p className="text-[11px] text-slate-500 dark:text-slate-400 text-center leading-relaxed max-w-xs mx-auto">
              Provide your email address below, and we will send you a secure link to reset your container password.
            </p>

            <div>
              <Input
                label="Registered Email Address"
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

            <button
              type="submit"
              disabled={submitting}
              className="w-full flex justify-center items-center py-2.5 px-4 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-500/10 hover:shadow-indigo-500/20 cursor-pointer focus:outline-none disabled:opacity-50 transition-all gap-2"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating key...
                </>
              ) : (
                "Request reset link"
              )}
            </button>

            <Link
              href="/login"
              className="w-full flex justify-center items-center py-2.5 px-4 rounded-xl text-xs font-bold bg-transparent text-slate-550 dark:text-slate-400 hover:text-slate-850 dark:hover:text-slate-200 cursor-pointer focus:outline-none transition-all gap-1.5 mt-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Cancel and return
            </Link>
          </form>
        )}
      </Card>
    </div>
  );
}

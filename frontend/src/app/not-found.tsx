"use client";

import React from "react";
import Link from "next/link";
import { Compass, Home } from "lucide-react";
import { PageWrapper } from "@/layouts/PageWrapper";
import { SectionContainer } from "@/layouts/SectionContainer";

export default function NotFound() {
  return (
    <PageWrapper className="min-h-screen flex items-center justify-center bg-white dark:bg-slate-950">
      <SectionContainer className="text-center flex flex-col items-center max-w-md">
        {/* Animated Visual Compass */}
        <div className="h-16 w-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-6 shadow-md shadow-indigo-500/5">
          <Compass className="h-8 w-8 animate-spin-slow" />
        </div>

        <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight mb-3">
          404 - Lost Course
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-8 leading-relaxed max-w-xs">
          The coordinates you requested do not exist. Your LifePilot copilot has diverted to home
          base.
        </p>

        <Link
          href="/"
          className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20 hover:shadow-indigo-600/35 transition-all hover:-translate-y-0.5 active:scale-[0.98] cursor-pointer"
        >
          <Home className="h-4 w-4" />
          Return Home
        </Link>
      </SectionContainer>
    </PageWrapper>
  );
}

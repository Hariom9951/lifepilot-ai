"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", label, helperText, error, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5 text-left">
        {label && (
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-350">
            {label}
          </label>
        )}
        <input
          type={type}
          className={cn(
            "w-full px-3 py-2 text-sm rounded-lg border bg-transparent text-slate-900 placeholder-slate-400 dark:text-slate-100 dark:placeholder-slate-600 focus:outline-none focus:ring-2 transition-all duration-250",
            error
              ? "border-red-500 focus:ring-red-500/20 focus:border-red-500"
              : "border-slate-200/60 dark:border-slate-800/60 focus:ring-indigo-500/20 focus:border-indigo-500 dark:focus:ring-indigo-500/30 dark:focus:border-indigo-400",
            className
          )}
          ref={ref}
          {...props}
        />
        {helperText && (
          <p
            className={cn(
              "text-[10px] font-medium leading-normal",
              error ? "text-red-500" : "text-slate-500 dark:text-slate-500"
            )}
          >
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

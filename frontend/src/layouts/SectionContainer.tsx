"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface SectionContainerProps extends React.HTMLAttributes<HTMLElement> {
  as?: "section" | "div" | "article";
}

export function SectionContainer({
  children,
  className,
  as: Component = "section",
  ...props
}: SectionContainerProps) {
  return (
    <Component
      className={cn("w-full max-w-5xl mx-auto px-4 py-16 md:py-24 relative", className)}
      {...props}
    >
      {children}
    </Component>
  );
}

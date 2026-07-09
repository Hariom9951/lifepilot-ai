"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface DropdownContextProps {
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

const DropdownContext = React.createContext<DropdownContextProps | null>(null);

export interface DropdownProps {
  children: React.ReactNode;
  className?: string;
}

export function Dropdown({ children, className }: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <DropdownContext.Provider value={{ isOpen, setIsOpen }}>
      <div className={cn("relative inline-block text-left", className)} ref={containerRef}>
        {children}
      </div>
    </DropdownContext.Provider>
  );
}

export interface DropdownTriggerProps {
  children: React.ReactNode;
}

export function DropdownTrigger({ children }: DropdownTriggerProps) {
  const context = React.useContext(DropdownContext);
  if (!context) throw new Error("DropdownTrigger must be used inside Dropdown");

  const child = React.Children.only(children) as React.ReactElement<{
    onClick?: React.MouseEventHandler;
    className?: string;
  }>;

  return React.cloneElement(child, {
    onClick: (e: React.MouseEvent) => {
      context.setIsOpen(!context.isOpen);
      if (child.props.onClick) {
        child.props.onClick(e);
      }
    },
    className: cn(child.props.className, "cursor-pointer"),
  });
}

export interface DropdownMenuProps {
  children: React.ReactNode;
  align?: "left" | "right";
  className?: string;
}

export function DropdownMenu({ children, align = "right", className }: DropdownMenuProps) {
  const context = React.useContext(DropdownContext);
  if (!context) throw new Error("DropdownMenu must be used inside Dropdown");

  return (
    <AnimatePresence>
      {context.isOpen && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 5 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 5 }}
          transition={{ duration: 0.15, ease: "easeOut" }}
          className={cn(
            "absolute z-50 mt-2 w-48 rounded-xl border border-slate-200/50 bg-white p-1 shadow-lg dark:border-slate-800/40 dark:bg-slate-900/90 backdrop-blur-md focus:outline-none",
            align === "right" ? "right-0" : "left-0",
            className
          )}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export type DropdownItemProps = React.ButtonHTMLAttributes<HTMLButtonElement>;

export function DropdownItem({ children, className, onClick, ...props }: DropdownItemProps) {
  const context = React.useContext(DropdownContext);
  if (!context) throw new Error("DropdownItem must be used inside Dropdown");

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    context.setIsOpen(false);
    if (onClick) onClick(e);
  };

  return (
    <button
      onClick={handleClick}
      className={cn(
        "w-full text-left px-3 py-2 text-xs font-semibold rounded-lg text-slate-650 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-950/60 hover:text-slate-900 dark:hover:text-slate-100 transition-colors select-none cursor-pointer focus:outline-none",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

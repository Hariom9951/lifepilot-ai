import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "../styles/globals.css";
import { ThemeProvider } from "@/providers/ThemeProvider";
import { ToastProvider } from "@/components/ui/toast";
import CommandPalette from "@/components/CommandPalette";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "LifePilot AI - Personal Life Operating System",
    template: "%s | LifePilot AI",
  },
  description:
    "A premium, unified personal operating system linking tasks, habits, expenses, notes, and local AI retrieval (RAG) in a private container.",
  keywords: [
    "Life operating system",
    "AI assistant",
    "Personal dashboard",
    "Habit streaks",
    "Budget envelopes",
    "Local RAG",
    "SaaS framework",
  ],
  authors: [{ name: "LifePilot AI Team", url: "https://lifepilot.ai" }],
  openGraph: {
    title: "LifePilot AI - Personal Life Operating System",
    description:
      "A premium, unified personal operating system linking tasks, habits, expenses, notes, and local AI retrieval (RAG) in a private container.",
    url: "https://lifepilot.ai",
    siteName: "LifePilot AI",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "LifePilot AI - Personal Life Operating System",
    description:
      "A premium, unified personal operating system linking tasks, habits, expenses, notes, and local AI retrieval (RAG) in a private container.",
    creator: "@lifepilot_ai",
  },
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-white text-slate-900 transition-colors duration-300 dark:bg-slate-950 dark:text-slate-100">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <ToastProvider>
            <CommandPalette />
            {children}
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

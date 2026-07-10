"use client";

import React, { useState, useEffect } from "react";
import { User as UserIcon, Bell, Globe, Cpu, Sun, Moon, Laptop } from "lucide-react";
import { useTheme } from "next-themes";
import Image from "next/image";
import { PageWrapper } from "@/layouts/PageWrapper";
import { SectionContainer } from "@/layouts/SectionContainer";
import Navbar from "@/layouts/Navbar";
import LandingFooter from "@/features/landing/components/LandingFooter";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/toast";
import { useAuthStore } from "@/store/authStore";
import { apiClient } from "@/config/axios";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { toast } = useToast();
  const { user, updateUser } = useAuthStore();

  const [profile, setProfile] = useState(() => ({
    name: user?.full_name || "",
    email: user?.email || "",
    avatar_url: user?.avatar_url || "",
    timezone: user?.timezone || "UTC",
    language: user?.language || "en",
  }));

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!user) return;

    let active = true;
    const timer = setTimeout(() => {
      if (active) {
        setProfile({
          name: user.full_name,
          email: user.email,
          avatar_url: user.avatar_url || "",
          timezone: user.timezone,
          language: user.language,
        });
      }
    }, 0);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [user]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const response = await apiClient.patch("/users/profile", {
        full_name: profile.name,
        avatar_url: profile.avatar_url || null,
        timezone: profile.timezone,
        language: profile.language,
      });
      updateUser(response.data.data);
      toast("Settings changes saved successfully!", "success");
    } catch (error) {
      const axiosError = error as { response?: { data?: { message?: string } } };
      const msg = axiosError.response?.data?.message || "Failed to update profile settings.";
      toast(msg, "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <PageWrapper className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 font-sans">
      <Navbar />

      <SectionContainer className="max-w-4xl py-12 md:py-16">
        <div className="border-b border-slate-200/60 dark:border-slate-900 pb-8 mb-10">
          <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white mb-2">
            Settings Console
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Configure system themes, user profiles, alert notifications, and local workspace
            connections.
          </p>
        </div>

        <Tabs defaultValue="profile" className="w-full">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Tabs Navigation Sidebar */}
            <div className="md:col-span-1">
              <TabsList className="flex flex-row md:flex-col bg-transparent border-0 gap-1 p-0 items-start w-full overflow-x-auto md:overflow-x-visible">
                <TabsTrigger
                  value="profile"
                  className="w-full text-left justify-start md:py-2.5 px-3 border border-transparent aria-selected:bg-indigo-500/10 aria-selected:text-indigo-650 dark:aria-selected:bg-indigo-500/15 dark:aria-selected:text-indigo-400"
                >
                  <UserIcon className="h-4 w-4 mr-2 inline" />
                  Profile
                </TabsTrigger>
                <TabsTrigger
                  value="theme"
                  className="w-full text-left justify-start md:py-2.5 px-3 border border-transparent aria-selected:bg-indigo-500/10 aria-selected:text-indigo-650 dark:aria-selected:bg-indigo-500/15 dark:aria-selected:text-indigo-400"
                >
                  <Sun className="h-4 w-4 mr-2 inline" />
                  Appearance
                </TabsTrigger>
                <TabsTrigger
                  value="notifications"
                  className="w-full text-left justify-start md:py-2.5 px-3 border border-transparent aria-selected:bg-indigo-500/10 aria-selected:text-indigo-650 dark:aria-selected:bg-indigo-500/15 dark:aria-selected:text-indigo-400"
                >
                  <Bell className="h-4 w-4 mr-2 inline" />
                  Notifications
                </TabsTrigger>
                <TabsTrigger
                  value="language"
                  className="w-full text-left justify-start md:py-2.5 px-3 border border-transparent aria-selected:bg-indigo-500/10 aria-selected:text-indigo-650 dark:aria-selected:bg-indigo-500/15 dark:aria-selected:text-indigo-400"
                >
                  <Globe className="h-4 w-4 mr-2 inline" />
                  Language
                </TabsTrigger>
                <TabsTrigger
                  value="integrations"
                  className="w-full text-left justify-start md:py-2.5 px-3 border border-transparent aria-selected:bg-indigo-500/10 aria-selected:text-indigo-650 dark:aria-selected:bg-indigo-500/15 dark:aria-selected:text-indigo-400"
                >
                  <Cpu className="h-4 w-4 mr-2 inline" />
                  Integrations
                </TabsTrigger>
              </TabsList>
            </div>

            {/* Tabs Content */}
            <div className="md:col-span-3">
              {/* Profile Settings */}
              <TabsContent value="profile">
                <Card className="p-6">
                  <form onSubmit={handleSave} className="space-y-6">
                    <div className="flex items-center gap-4 border-b border-slate-100 dark:border-slate-900 pb-4 mb-4">
                      <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-605 flex items-center justify-center text-white font-bold text-lg overflow-hidden select-none">
                        {profile.avatar_url ? (
                          <Image
                            src={profile.avatar_url}
                            alt="Avatar"
                            width={48}
                            height={48}
                            unoptimized
                            className="h-full w-full object-cover"
                          />
                        ) : profile.name ? (
                          profile.name
                            .split(" ")
                            .map((n) => n[0])
                            .join("")
                        ) : (
                          "U"
                        )}
                      </div>
                      <div>
                        <h3 className="text-xs font-black text-slate-800 dark:text-slate-200">
                          Profile Information
                        </h3>
                        <p className="text-[10px] text-slate-450 dark:text-slate-500">
                          Enter your details below to update your account identity profiles.
                        </p>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <Input
                        label="Full Name"
                        value={profile.name}
                        onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                        required
                      />
                      <Input
                        label="Email Address"
                        type="email"
                        value={profile.email}
                        disabled
                        required
                      />
                      <Input
                        label="Avatar Image URL"
                        type="text"
                        value={profile.avatar_url}
                        onChange={(e) => setProfile({ ...profile, avatar_url: e.target.value })}
                        placeholder="https://example.com/avatar.jpg"
                      />
                      <div>
                        <label className="block text-[11px] font-bold text-slate-505 dark:text-slate-400 mb-1.5 flex items-center gap-1">
                          Workspace Timezone
                        </label>
                        <select
                          value={profile.timezone}
                          onChange={(e) => setProfile({ ...profile, timezone: e.target.value })}
                          className="w-full text-xs px-3 py-2 bg-white dark:bg-slate-900/50 border border-slate-250 dark:border-slate-800 rounded-lg text-slate-800 dark:text-slate-202 outline-none focus:border-indigo-500"
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
                    </div>

                    <button
                      type="submit"
                      disabled={saving}
                      className="px-4 py-2 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-500/10 hover:shadow-indigo-500/20 cursor-pointer focus:outline-none disabled:opacity-50"
                    >
                      {saving ? "Saving Changes..." : "Save Changes"}
                    </button>
                  </form>
                </Card>
              </TabsContent>

              {/* Theme Settings */}
              <TabsContent value="theme">
                <Card className="p-6 space-y-6">
                  <div className="border-b border-slate-100 dark:border-slate-900 pb-4">
                    <h3 className="text-xs font-black text-slate-800 dark:text-slate-200 mb-1">
                      Theme Selection
                    </h3>
                    <p className="text-[10px] text-slate-450 dark:text-slate-500">
                      Customize how LifePilot AI looks on your screen.
                    </p>
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    <button
                      onClick={() => {
                        setTheme("light");
                        toast("Changed theme to Light", "info");
                      }}
                      className={`flex flex-col items-center gap-2 p-4 rounded-xl border transition-all cursor-pointer ${
                        theme === "light"
                          ? "border-indigo-500 bg-indigo-500/5 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-bold"
                          : "border-slate-200/50 bg-white hover:border-slate-300 text-slate-500 dark:border-slate-850 dark:bg-slate-900/40"
                      }`}
                    >
                      <Sun className="h-5 w-5" />
                      <span className="text-[10px] font-mono tracking-wider uppercase">Light</span>
                    </button>

                    <button
                      onClick={() => {
                        setTheme("dark");
                        toast("Changed theme to Dark", "info");
                      }}
                      className={`flex flex-col items-center gap-2 p-4 rounded-xl border transition-all cursor-pointer ${
                        theme === "dark"
                          ? "border-indigo-500 bg-indigo-500/5 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-bold"
                          : "border-slate-200/50 bg-white hover:border-slate-300 text-slate-500 dark:border-slate-850 dark:bg-slate-900/40"
                      }`}
                    >
                      <Moon className="h-5 w-5" />
                      <span className="text-[10px] font-mono tracking-wider uppercase">Dark</span>
                    </button>

                    <button
                      onClick={() => {
                        setTheme("system");
                        toast("Theme synced to System", "info");
                      }}
                      className={`flex flex-col items-center gap-2 p-4 rounded-xl border transition-all cursor-pointer ${
                        theme === "system"
                          ? "border-indigo-500 bg-indigo-500/5 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-bold"
                          : "border-slate-200/50 bg-white hover:border-slate-300 text-slate-500 dark:border-slate-850 dark:bg-slate-900/40"
                      }`}
                    >
                      <Laptop className="h-5 w-5" />
                      <span className="text-[10px] font-mono tracking-wider uppercase">System</span>
                    </button>
                  </div>
                </Card>
              </TabsContent>

              {/* Notifications Settings */}
              <TabsContent value="notifications">
                <Card className="p-6 space-y-6">
                  <div className="border-b border-slate-100 dark:border-slate-900 pb-4">
                    <h3 className="text-xs font-black text-slate-800 dark:text-slate-200 mb-1">
                      Notification Preferences
                    </h3>
                    <p className="text-[10px] text-slate-450 dark:text-slate-500">
                      Decide what logs or events trigger user notifications.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between py-2 border-b border-slate-100/50 dark:border-slate-900/50">
                      <div>
                        <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">
                          Daily Habit Reminders
                        </h4>
                        <p className="text-[10px] text-slate-400 dark:text-slate-500">
                          Trigger habit checklist review at morning standup.
                        </p>
                      </div>
                      <Badge variant="success">Active</Badge>
                    </div>

                    <div className="flex items-center justify-between py-2 border-b border-slate-100/50 dark:border-slate-900/50">
                      <div>
                        <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">
                          Budget Limit Warnings
                        </h4>
                        <p className="text-[10px] text-slate-400 dark:text-slate-500">
                          Alert when expense records approach budget thresholds.
                        </p>
                      </div>
                      <Badge variant="success">Active</Badge>
                    </div>

                    <div className="flex items-center justify-between py-2">
                      <div>
                        <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">
                          Weekly Sync Reports
                        </h4>
                        <p className="text-[10px] text-slate-400 dark:text-slate-500">
                          Summarize habit scores, tasks closed, and budgets saved.
                        </p>
                      </div>
                      <Badge variant="outline">Paused</Badge>
                    </div>
                  </div>
                </Card>
              </TabsContent>

              {/* Language Settings */}
              <TabsContent value="language">
                <Card className="p-6 space-y-6">
                  <div className="border-b border-slate-100 dark:border-slate-900 pb-4">
                    <h3 className="text-xs font-black text-slate-800 dark:text-slate-200 mb-1">
                      Localization Settings
                    </h3>
                    <p className="text-[10px] text-slate-450 dark:text-slate-500">
                      Set your default workspace rendering language.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <select className="w-full text-xs px-3 py-2 bg-transparent border border-slate-200/60 dark:border-slate-800 rounded-lg text-slate-800 dark:text-slate-200 outline-none">
                        <option>English (United States)</option>
                        <option>Spanish (Español)</option>
                        <option>German (Deutsch)</option>
                        <option>French (Français)</option>
                      </select>
                    </div>
                  </div>
                </Card>
              </TabsContent>

              {/* Integrations Settings */}
              <TabsContent value="integrations">
                <Card className="p-6 space-y-6">
                  <div className="border-b border-slate-100 dark:border-slate-900 pb-4">
                    <h3 className="text-xs font-black text-slate-800 dark:text-slate-200 mb-1">
                      External Integrations
                    </h3>
                    <p className="text-[10px] text-slate-450 dark:text-slate-500">
                      Connect your secure container to databases and local models.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-950/20 flex items-center justify-between">
                      <div className="space-y-1">
                        <span className="text-[9px] font-bold font-mono tracking-widest uppercase text-slate-450 dark:text-slate-500">
                          Database Storage
                        </span>
                        <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">
                          PostgreSQL 16 Connector
                        </h4>
                      </div>
                      <Badge variant="outline">Disconnected</Badge>
                    </div>

                    <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-950/20 flex items-center justify-between">
                      <div className="space-y-1">
                        <span className="text-[9px] font-bold font-mono tracking-widest uppercase text-slate-450 dark:text-slate-500">
                          Fast Cache Store
                        </span>
                        <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">
                          Redis Database Connection
                        </h4>
                      </div>
                      <Badge variant="outline">Disconnected</Badge>
                    </div>

                    <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-950/20 flex items-center justify-between">
                      <div className="space-y-1">
                        <span className="text-[9px] font-bold font-mono tracking-widest uppercase text-slate-450 dark:text-slate-500">
                          LLM Context
                        </span>
                        <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">
                          Gemini API Key
                        </h4>
                      </div>
                      <Badge variant="outline">Disconnected</Badge>
                    </div>
                  </div>
                </Card>
              </TabsContent>
            </div>
          </div>
        </Tabs>
      </SectionContainer>

      <LandingFooter />
    </PageWrapper>
  );
}

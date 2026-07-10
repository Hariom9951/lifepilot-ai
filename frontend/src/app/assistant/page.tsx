"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  Send,
  Trash2,
  Plus,
  MessageSquare,
  Bot,
  User as UserIcon,
  Sparkles,
  Calendar,
  Flame,
  Target,
  Coins,
  Activity,
  ArrowRight,
  Loader2,
  Clock,
  ChevronRight,
} from "lucide-react";
import { PageWrapper } from "@/layouts/PageWrapper";
import Navbar from "@/layouts/Navbar";
import { apiClient } from "@/config/axios";
import { useToast } from "@/components/ui/toast";
import { useAuthStore } from "@/store/authStore";
import type {
  ChatAction,
  ChatHistoryItem,
  ChatResponse,
  ChatHistoryResponse,
} from "@/types/assistant";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function AssistantPage() {
  const { user } = useAuthStore();
  const { toast } = useToast();

  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [historyItems, setHistoryItems] = useState<ChatHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  // Recommendations and actions from the latest assistant message
  const [activeRecommendations, setActiveRecommendations] = useState<string[]>([]);
  const [activeActions, setActiveActions] = useState<ChatAction[]>([]);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Suggested quick prompts
  const suggestedQuestions = [
    { label: "What should I do today?", prompt: "What should I do today?" },
    { label: "Show today's tasks.", prompt: "Show today's tasks." },
    { label: "Goal progress.", prompt: "Which goal am I closest to completing?" },
    { label: "Budget status.", prompt: "How is my budget?" },
    { label: "Show my habits.", prompt: "How are my habits?" },
    { label: "Summarize my week.", prompt: "Summarize my productivity." },
  ];

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const [pollHistoryTick, setPollHistoryTick] = useState(0);

  // Load chat history on mount
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await apiClient.get<{ data: ChatHistoryResponse }>("/assistant/history");
        if (!cancelled) setHistoryItems(res.data.data.items || []);
      } catch {
        if (!cancelled) toast("Failed to load chat history.", "error");
      } finally {
        if (!cancelled) setLoadingHistory(false);
      }
    }
    if (user) {
      void load();
    }
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, pollHistoryTick]);

  // Group history items by conversation_id to display in the sidebar
  const getUniqueConversations = () => {
    const map = new Map<string, ChatHistoryItem>();
    // Iterate backwards so we keep the newest message per conversation
    for (let i = historyItems.length - 1; i >= 0; i--) {
      const item = historyItems[i];
      map.set(item.conversation_id, item);
    }
    return Array.from(map.values()).sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  };

  const conversations = getUniqueConversations();

  // Load a conversation from history
  const loadConversation = (conversationId: string) => {
    const sessionMessages = historyItems
      .filter((item) => item.conversation_id === conversationId)
      // Order oldest to newest
      .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

    const formattedMessages: Message[] = [];
    sessionMessages.forEach((item) => {
      formattedMessages.push({
        role: "user",
        content: item.user_message,
        timestamp: new Date(item.created_at),
      });
      formattedMessages.push({
        role: "assistant",
        content: item.assistant_message,
        timestamp: new Date(item.created_at),
      });
    });

    setMessages(formattedMessages);
    setActiveConversationId(conversationId);

    // Hydrate latest recommendations & actions
    if (sessionMessages.length > 0) {
      const latest = sessionMessages[sessionMessages.length - 1];
      setActiveRecommendations(latest.recommendations || []);
      setActiveActions(latest.actions || []);
    } else {
      setActiveRecommendations([]);
      setActiveActions([]);
    }
  };

  // Start new conversation
  const startNewConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
    setActiveRecommendations([]);
    setActiveActions([]);
  };

  // Clear all history
  const handleClearHistory = async () => {
    if (!confirm("Are you sure you want to clear your chat history permanently?")) return;
    try {
      await apiClient.delete("/assistant/history");
      setHistoryItems([]);
      startNewConversation();
      toast("History deleted successfully.", "success");
    } catch {
      toast("Could not delete chat history.", "error");
    }
  };

  // Trigger typed action logic (e.g. clicking card button)
  const handleActionClick = (action: ChatAction) => {
    toast(`Executing action: ${action.label}`, "info");
    // Expandable for actual Phase 9 redirect/execution if desired
  };

  // Send message
  const handleSendMessage = async (textToSend: string) => {
    if (!textToSend.trim() || isStreaming || isTyping) return;

    setInputMessage("");
    const userMsg: Message = {
      role: "user",
      content: textToSend,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const response = await apiClient.post<{ data: ChatResponse }>("/assistant/chat", {
        message: textToSend,
        conversation_id: activeConversationId || null,
      });

      const data = response.data.data;
      if (!activeConversationId) {
        setActiveConversationId(data.conversation_id);
      }

      // Simulate streaming response
      setIsTyping(false);
      setIsStreaming(true);

      const fullReply = data.response;
      let currentLength = 0;
      const step = Math.ceil(fullReply.length / 30); // stream in ~30 chunks
      let streamedText = "";

      const assistantMsg: Message = {
        role: "assistant",
        content: "",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      const interval = setInterval(() => {
        currentLength += step;
        if (currentLength >= fullReply.length) {
          streamedText = fullReply;
          clearInterval(interval);
          setIsStreaming(false);
          // Sync recommendations and actions once fully loaded
          setActiveRecommendations(data.recommendations || []);
          setActiveActions(data.actions || []);
          setPollHistoryTick((t) => t + 1); // reload history panel
        } else {
          streamedText = fullReply.slice(0, currentLength) + " ▌";
        }

        setMessages((prev) => {
          const updated = [...prev];
          if (updated.length > 0) {
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: streamedText,
            };
          }
          return updated;
        });
      }, 35);
    } catch {
      setIsTyping(false);
      toast("Error querying assistant service.", "error");
    }
  };

  // Markdown inline formatter
  const formatInlineMarkdown = (text: string): React.ReactNode[] => {
    const parts = text.split(/(\*\*.*?\*\*|`.*?`|\*.*?\*)/g);
    return parts.map((part, idx) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={idx} className="font-extrabold text-slate-900 dark:text-white">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith("*") && part.endsWith("*")) {
        return (
          <em key={idx} className="italic text-slate-800 dark:text-slate-200">
            {part.slice(1, -1)}
          </em>
        );
      }
      if (part.startsWith("`") && part.endsWith("`")) {
        return (
          <code
            key={idx}
            className="bg-slate-150 dark:bg-slate-900/60 px-1.5 py-0.5 rounded font-mono text-[10.5px] text-indigo-600 dark:text-indigo-400 border border-slate-200/40 dark:border-slate-800/40"
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  // Custom Markdown parser
  const renderMarkdown = (text: string) => {
    const parts = text.split(/(```[\s\S]*?```)/g);
    return parts.map((part, index) => {
      if (part.startsWith("```")) {
        const match = part.match(/```(\w*)\n?([\s\S]*?)```/);
        const language = match ? match[1] : "";
        const code = match ? match[2].trim() : part.slice(3, -3).trim();
        return (
          <pre
            key={index}
            className="bg-slate-950 text-slate-100 p-4 rounded-xl font-mono text-xs my-3 overflow-x-auto border border-slate-900 select-all"
          >
            {language && (
              <div className="text-[9px] text-slate-500 uppercase font-black mb-1 select-none">
                {language}
              </div>
            )}
            <code>{code}</code>
          </pre>
        );
      }

      const lines = part.split("\n");
      return lines.map((line, lineIdx) => {
        if (line.startsWith("### ")) {
          return (
            <h3
              key={`${index}-${lineIdx}`}
              className="text-sm font-black text-slate-900 dark:text-white mt-4 mb-1.5 flex items-center gap-1.5"
            >
              {formatInlineMarkdown(line.slice(4))}
            </h3>
          );
        } else if (line.startsWith("## ")) {
          return (
            <h2
              key={`${index}-${lineIdx}`}
              className="text-base font-black text-slate-900 dark:text-white mt-5 mb-2 border-b border-slate-100 dark:border-slate-900 pb-1"
            >
              {formatInlineMarkdown(line.slice(3))}
            </h2>
          );
        } else if (line.startsWith("# ")) {
          return (
            <h1
              key={`${index}-${lineIdx}`}
              className="text-lg font-black text-slate-900 dark:text-white mt-6 mb-3"
            >
              {formatInlineMarkdown(line.slice(2))}
            </h1>
          );
        }

        if (line.trim().startsWith("- ")) {
          return (
            <li
              key={`${index}-${lineIdx}`}
              className="ml-5 list-disc text-slate-700 dark:text-slate-350 text-xs my-1"
            >
              {formatInlineMarkdown(line.trim().slice(2))}
            </li>
          );
        }

        return (
          <p
            key={`${index}-${lineIdx}`}
            className="text-xs leading-relaxed text-slate-700 dark:text-slate-305 my-1"
          >
            {formatInlineMarkdown(line)}
          </p>
        );
      });
    });
  };

  // Helper to map card types/labels to beautiful visual categories
  const getCardDetails = (rec: string) => {
    const lower = rec.toLowerCase();
    if (lower.includes("streak") || lower.includes("habit")) {
      return {
        icon: <Flame className="h-4.5 w-4.5 text-amber-500" />,
        theme: "from-amber-500/10 to-orange-500/5 border-amber-500/20 dark:border-amber-500/10",
        badge: "HABIT STREAK",
        badgeColor: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
      };
    }
    if (lower.includes("goal")) {
      return {
        icon: <Target className="h-4.5 w-4.5 text-emerald-500" />,
        theme: "from-emerald-500/10 to-teal-500/5 border-emerald-500/20 dark:border-emerald-500/10",
        badge: "GOAL PROGRESS",
        badgeColor: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
      };
    }
    if (lower.includes("spend") || lower.includes("budget") || lower.includes("cost")) {
      return {
        icon: <Coins className="h-4.5 w-4.5 text-rose-500" />,
        theme: "from-rose-500/10 to-red-500/5 border-rose-500/20 dark:border-rose-500/10",
        badge: "BUDGET ALERT",
        badgeColor: "bg-rose-500/10 text-rose-600 dark:text-rose-400",
      };
    }
    if (lower.includes("productivity") || lower.includes("health") || lower.includes("score")) {
      return {
        icon: <Activity className="h-4.5 w-4.5 text-violet-500" />,
        theme: "from-violet-500/10 to-indigo-500/5 border-violet-500/20 dark:border-violet-500/10",
        badge: "PRODUCTIVITY",
        badgeColor: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
      };
    }
    return {
      icon: <Calendar className="h-4.5 w-4.5 text-blue-500" />,
      theme: "from-blue-500/10 to-sky-500/5 border-blue-500/20 dark:border-blue-500/10",
      badge: "SCHEDULE SUGGESTION",
      badgeColor: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
    };
  };

  if (!user) return null;

  return (
    <PageWrapper className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 font-sans transition-colors duration-300 flex flex-col">
      <Navbar />

      <div className="flex-1 flex overflow-hidden max-w-6xl w-full mx-auto relative px-4 md:px-6">
        {/* Main layout container split in two panels: Sidebar and Chat Workspace */}
        <div className="flex-1 flex bg-white/70 dark:bg-slate-900/40 rounded-3xl border border-slate-200/55 dark:border-slate-800/45 my-6 overflow-hidden shadow-2xl backdrop-blur-xl relative">
          {/* Sidebar Panel - Conversation History */}
          <aside className="w-64 border-r border-slate-200/60 dark:border-slate-800/60 flex flex-col bg-slate-50/50 dark:bg-slate-950/20 shrink-0 hidden md:flex">
            {/* Sidebar Action Headers */}
            <div className="p-4 border-b border-slate-200/60 dark:border-slate-800/60 space-y-2">
              <button
                onClick={startNewConversation}
                className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-indigo-650 hover:bg-indigo-600 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-indigo-500/10 hover:shadow-indigo-500/20 hover:scale-[1.01] cursor-pointer"
              >
                <Plus className="h-4.5 w-4.5" />
                New Chat
              </button>
            </div>

            {/* Conversation list */}
            <div className="flex-1 overflow-y-auto p-3 space-y-1">
              <span className="text-[10px] font-bold text-slate-400 px-3 tracking-widest font-mono block mb-2 uppercase">
                RECENT SESSIONS
              </span>

              {loadingHistory ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-5 w-5 text-indigo-500 animate-spin" />
                </div>
              ) : conversations.length === 0 ? (
                <div className="text-center py-8 text-[11px] text-slate-450 dark:text-slate-550 select-none">
                  No active logs.
                </div>
              ) : (
                conversations.map((item) => {
                  const isActive = item.conversation_id === activeConversationId;
                  return (
                    <button
                      key={item.id}
                      onClick={() => loadConversation(item.conversation_id)}
                      className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-left transition-all text-xs font-medium cursor-pointer group ${
                        isActive
                          ? "bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 font-bold border-l-3 border-indigo-500 pl-2.5"
                          : "hover:bg-slate-100 dark:hover:bg-slate-900/60 text-slate-650 dark:text-slate-400"
                      }`}
                    >
                      <MessageSquare className="h-4 w-4 shrink-0 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300" />
                      <span className="truncate flex-1">
                        {item.user_message.slice(0, 32) || "Chat Session"}
                      </span>
                      <ChevronRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  );
                })
              )}
            </div>

            {/* Sidebar Foot Action */}
            {historyItems.length > 0 && (
              <div className="p-3 border-t border-slate-200/60 dark:border-slate-800/60">
                <button
                  onClick={handleClearHistory}
                  className="w-full flex items-center justify-center gap-1.5 py-2 px-3 border border-slate-200 dark:border-slate-800 hover:border-rose-200 dark:hover:border-rose-950 hover:bg-rose-50/30 dark:hover:bg-rose-950/10 text-slate-450 dark:text-slate-500 hover:text-rose-600 dark:hover:text-rose-400 rounded-xl text-xs font-bold transition-all cursor-pointer"
                >
                  <Trash2 className="h-4 w-4" />
                  Clear All History
                </button>
              </div>
            )}
          </aside>

          {/* Chat Panel & Cards Viewport */}
          <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
            {/* Left side: Chat Console */}
            <main className="flex-1 flex flex-col overflow-hidden bg-white/40 dark:bg-slate-900/10">
              {/* Header Info */}
              <div className="px-6 py-4 border-b border-slate-200/50 dark:border-slate-800/40 bg-white/60 dark:bg-slate-900/30 backdrop-blur flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-8.5 w-8.5 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-650 flex items-center justify-center shadow shadow-indigo-500/20">
                    <Sparkles className="h-4.5 w-4.5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-xs font-black text-slate-850 dark:text-white tracking-tight flex items-center gap-1.5">
                      Conversational AI Pilot
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    </h2>
                    <p className="text-[9px] font-bold text-slate-400 tracking-wider font-mono uppercase">
                      Active Sandbox Node
                    </p>
                  </div>
                </div>

                {/* Mobile Reset trigger */}
                <button
                  onClick={startNewConversation}
                  className="md:hidden flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900 cursor-pointer"
                  title="New conversation"
                >
                  <Plus className="h-4.5 w-4.5 text-slate-500" />
                </button>
              </div>

              {/* Message Streams viewport */}
              <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 scrollbar-thin scrollbar-thumb-slate-250 dark:scrollbar-thumb-slate-800">
                {messages.length === 0 ? (
                  // Initial Screen when empty
                  <div className="h-full flex flex-col items-center justify-center max-w-md mx-auto text-center space-y-6 py-12 select-none">
                    <div className="h-16 w-16 rounded-3xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white shadow-xl shadow-indigo-500/20 animate-bounce">
                      <Bot className="h-9 w-9" />
                    </div>
                    <div className="space-y-2">
                      <h3 className="text-base font-black tracking-tight text-slate-900 dark:text-white">
                        Welcome to LifePilot AI Assistant
                      </h3>
                      <p className="text-xs text-slate-450 dark:text-slate-450 leading-relaxed">
                        I am synced with your active containers. Ask me about your budget status,
                        pending tasks, habit streaks, or productivity analytics.
                      </p>
                    </div>

                    {/* suggested list */}
                    <div className="w-full pt-4 space-y-2.5">
                      <span className="text-[10px] font-black text-slate-400 font-mono tracking-widest block uppercase">
                        SUGGESTED QUESTIONS
                      </span>
                      <div className="grid grid-cols-2 gap-2 text-left">
                        {suggestedQuestions.map((q, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSendMessage(q.prompt)}
                            className="p-3 bg-white hover:bg-indigo-50/30 dark:bg-slate-900/60 dark:hover:bg-indigo-950/20 rounded-2xl border border-slate-200/50 hover:border-indigo-500/30 dark:border-slate-800/40 dark:hover:border-indigo-500/20 transition-all text-[11px] font-bold text-slate-700 dark:text-slate-300 hover:text-indigo-650 dark:hover:text-indigo-400 flex items-center justify-between cursor-pointer"
                          >
                            <span className="truncate mr-2">{q.label}</span>
                            <ChevronRight className="h-3 w-3 text-slate-400 dark:text-slate-600 shrink-0" />
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  // Chat message thread
                  <div className="space-y-4">
                    {messages.map((msg, idx) => {
                      const isBot = msg.role === "assistant";
                      return (
                        <div
                          key={idx}
                          className={`flex items-start gap-3.5 max-w-2xl ${
                            isBot ? "" : "ml-auto flex-row-reverse"
                          }`}
                        >
                          {/* Avatar icon */}
                          <div
                            className={`h-8 w-8 rounded-xl flex items-center justify-center shrink-0 shadow-md ${
                              isBot
                                ? "bg-gradient-to-br from-indigo-500 to-purple-650 text-white"
                                : "bg-slate-100 dark:bg-slate-800 text-slate-650 dark:text-slate-300"
                            }`}
                          >
                            {isBot ? (
                              <Bot className="h-4.5 w-4.5" />
                            ) : (
                              <UserIcon className="h-4.5 w-4.5" />
                            )}
                          </div>

                          {/* Message bubble */}
                          <div className="space-y-1">
                            <div
                              className={`px-4.5 py-3 rounded-2xl text-xs shadow-sm border ${
                                isBot
                                  ? "bg-white dark:bg-slate-900 border-slate-200/50 dark:border-slate-800/50 text-slate-800 dark:text-slate-200 rounded-tl-sm"
                                  : "bg-indigo-600 border-indigo-700 text-white rounded-tr-sm"
                              }`}
                            >
                              {isBot ? renderMarkdown(msg.content) : msg.content}
                            </div>
                            <div
                              className={`text-[9px] text-slate-400 font-medium px-1 flex items-center gap-1 ${
                                isBot ? "" : "justify-end"
                              }`}
                            >
                              <Clock className="h-2.5 w-2.5" />
                              {msg.timestamp.toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </div>
                          </div>
                        </div>
                      );
                    })}

                    {/* Typing Indicator */}
                    {isTyping && (
                      <div className="flex items-start gap-3.5 max-w-lg">
                        <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-650 text-white flex items-center justify-center shrink-0 shadow-md">
                          <Bot className="h-4.5 w-4.5 animate-spin" />
                        </div>
                        <div className="bg-white dark:bg-slate-900 border border-slate-200/50 dark:border-slate-800/50 px-4.5 py-3 rounded-2xl rounded-tl-sm flex items-center gap-1 shadow-sm">
                          <span
                            className="h-1.5 w-1.5 bg-indigo-500 dark:bg-indigo-400 rounded-full animate-bounce"
                            style={{ animationDelay: "0ms" }}
                          />
                          <span
                            className="h-1.5 w-1.5 bg-indigo-500 dark:bg-indigo-400 rounded-full animate-bounce"
                            style={{ animationDelay: "150ms" }}
                          />
                          <span
                            className="h-1.5 w-1.5 bg-indigo-500 dark:bg-indigo-400 rounded-full animate-bounce"
                            style={{ animationDelay: "300ms" }}
                          />
                        </div>
                      </div>
                    )}

                    <div ref={chatEndRef} />
                  </div>
                )}
              </div>

              {/* Chat Input deck */}
              <div className="p-4 border-t border-slate-200/50 dark:border-slate-800/40 bg-white/60 dark:bg-slate-900/30 backdrop-blur">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    void handleSendMessage(inputMessage);
                  }}
                  className="flex items-center gap-2 bg-white dark:bg-slate-950 border border-slate-200/60 dark:border-slate-800/60 rounded-2xl px-4 py-2.5 shadow-md shadow-slate-100/50 dark:shadow-none focus-within:border-indigo-500/70 focus-within:ring-2 focus-within:ring-indigo-500/10 dark:focus-within:ring-indigo-500/5 transition-all"
                >
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Ask about goals, habits, budget, or tasks..."
                    disabled={isStreaming || isTyping}
                    className="flex-1 bg-transparent text-xs text-slate-850 dark:text-slate-100 outline-none placeholder-slate-400 disabled:opacity-60"
                  />
                  <button
                    type="submit"
                    disabled={!inputMessage.trim() || isStreaming || isTyping}
                    className="h-8 w-8 rounded-xl bg-indigo-650 hover:bg-indigo-600 disabled:bg-slate-100 dark:disabled:bg-slate-900 text-white disabled:text-slate-400 flex items-center justify-center shrink-0 transition-all cursor-pointer disabled:cursor-not-allowed hover:scale-[1.03]"
                  >
                    <Send className="h-3.5 w-3.5" />
                  </button>
                </form>
              </div>
            </main>

            {/* Right side: AI Cards (Recommendations deck) */}
            <aside className="w-full md:w-68 border-t md:border-t-0 md:border-l border-slate-200/60 dark:border-slate-800/60 flex flex-col p-4 bg-slate-50/20 dark:bg-slate-950/10 max-h-[300px] md:max-h-none overflow-y-auto">
              <span className="text-[10px] font-black text-slate-400 tracking-widest font-mono block mb-3 uppercase">
                AI RECOMMENDATIONS
              </span>

              {activeRecommendations.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-6 border border-dashed border-slate-200 dark:border-slate-800 rounded-2xl min-h-[120px] select-none">
                  <Bot className="h-5 w-5 text-slate-350 dark:text-slate-650 mb-2" />
                  <p className="text-[10px] text-slate-400 dark:text-slate-550 leading-relaxed">
                    Submit a query to generate contextual recommendations & actions.
                  </p>
                </div>
              ) : (
                <div className="space-y-3 flex-1">
                  {/* Map over latest recommendations array */}
                  {activeRecommendations.map((rec, index) => {
                    const card = getCardDetails(rec);
                    return (
                      <div
                        key={index}
                        className={`p-3.5 rounded-2xl bg-gradient-to-br ${card.theme} border flex flex-col gap-2 shadow-sm animate-fade-in`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span
                            className={`text-[8.5px] font-black tracking-wider px-2 py-0.5 rounded ${card.badgeColor}`}
                          >
                            {card.badge}
                          </span>
                          {card.icon}
                        </div>
                        <p className="text-[11px] font-bold text-slate-800 dark:text-slate-200 leading-snug">
                          {rec}
                        </p>
                      </div>
                    );
                  })}

                  {/* Actions deck below recommendations */}
                  {activeActions.length > 0 && (
                    <div className="pt-3 border-t border-slate-200/60 dark:border-slate-800/60 space-y-2">
                      <span className="text-[9px] font-bold text-slate-400 tracking-widest font-mono uppercase block mb-1">
                        SUGGESTED ACTIONS
                      </span>
                      {activeActions.map((action, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleActionClick(action)}
                          className="w-full flex items-center justify-between p-2.5 bg-white dark:bg-slate-900 border border-slate-200/50 hover:border-indigo-500 dark:border-slate-850 dark:hover:border-indigo-500/50 rounded-xl text-[10.5px] font-bold text-slate-700 dark:text-slate-300 hover:text-indigo-650 dark:hover:text-indigo-400 transition-all cursor-pointer group"
                        >
                          <span className="truncate mr-2">{action.label}</span>
                          <ArrowRight className="h-3 w-3 text-slate-400 group-hover:text-indigo-500 dark:group-hover:text-indigo-400 shrink-0 group-hover:translate-x-0.5 transition-all" />
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </aside>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}

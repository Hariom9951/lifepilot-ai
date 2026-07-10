import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { User } from "@/types/auth";
import axios from "axios";

interface AuthState {
  accessToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setSession: (accessToken: string, user: User) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  initializeAuth: () => Promise<void>;
  updateUser: (updatedUser: User) => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,
      isAuthenticated: false,
      isLoading: true, // Start in loading state until checked

      setSession: (accessToken: string, user: User) => {
        set({ accessToken, user, isAuthenticated: true, isLoading: false });
      },

      logout: () => {
        set({ accessToken: null, user: null, isAuthenticated: false, isLoading: false });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      updateUser: (updatedUser: User) => {
        set({ user: updatedUser });
      },

      initializeAuth: async () => {
        set({ isLoading: true });
        try {
          // Send request to /auth/refresh to check if cookie exists and silent login is possible
          const response = await axios.post(
            `${API_URL}/api/v1/auth/refresh`,
            {},
            { withCredentials: true }
          );
          const { access_token, user } = response.data.data;
          set({ accessToken: access_token, user, isAuthenticated: true });
        } catch {
          // If refresh fails, user is unauthenticated
          set({ accessToken: null, user: null, isAuthenticated: false });
        } finally {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: "lifepilot-auth-store",
      storage: createJSONStorage(() => localStorage),
      // Only persist user metadata, not the access token (for JWT security)
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

"use client";

import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest, setCsrfToken } from "@/lib/api-client";
import type { LoginResponse, MembershipSummary, UserProfile } from "@/lib/types";
import { useWorkspaceStore } from "@/store/workspace-store";

interface AuthContextValue {
  user: UserProfile | null;
  isLoading: boolean;
  activeMembership: MembershipSummary | null;
  setActiveMembershipId: (membershipId: string) => void;
  login: (email: string, password: string) => Promise<UserProfile>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const selectedMembershipId = useWorkspaceStore(
    (state) => state.selectedMembershipId
  );
  const setSelectedMembershipId = useWorkspaceStore(
    (state) => state.setSelectedMembershipId
  );
  const resetWorkspace = useWorkspaceStore((state) => state.resetWorkspace);

  const { data: user = null, isLoading, refetch } = useQuery<UserProfile | null>({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      try {
        return await apiRequest<UserProfile>("/auth/me");
      } catch {
        return null;
      }
    },
    retry: false,
    staleTime: 60_000,
  });

  const activeMemberships = React.useMemo(
    () => (user?.memberships || []).filter((m) => m.status === "active"),
    [user]
  );

  const activeMembership = React.useMemo(() => {
    if (activeMemberships.length === 0) return null;
    if (selectedMembershipId) {
      const match = activeMemberships.find((m) => m.id === selectedMembershipId);
      if (match) return match;
    }
    return activeMemberships[0];
  }, [activeMemberships, selectedMembershipId]);

  const login = React.useCallback(
    async (email: string, password: string): Promise<UserProfile> => {
      const data = await apiRequest<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setCsrfToken(data.csrf_token);
      queryClient.setQueryData(["auth", "me"], data.user);
      return data.user;
    },
    [queryClient]
  );

  const logout = React.useCallback(async () => {
    try {
      await apiRequest("/auth/logout", { method: "POST" });
    } finally {
      setCsrfToken(null);
      resetWorkspace();
      queryClient.setQueryData(["auth", "me"], null);
      queryClient.clear();
    }
  }, [queryClient, resetWorkspace]);

  const refreshUser = React.useCallback(async () => {
    await refetch();
  }, [refetch]);

  const value = React.useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      activeMembership,
      setActiveMembershipId: setSelectedMembershipId,
      login,
      logout,
      refreshUser,
    }),
    [user, isLoading, activeMembership, login, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = React.useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside <AuthProvider>.");
  }
  return ctx;
}

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

interface WorkspaceUiState {
  /** Selected active school membership ID (for users/parents with multiple schools). */
  selectedMembershipId: string | null;
  /** Selected child student_user_id in the Parent portal. */
  selectedChildId: string | null;
  /** Desktop sidebar collapsed preference. */
  sidebarCollapsed: boolean;
  setSelectedMembershipId: (id: string | null) => void;
  setSelectedChildId: (id: string | null) => void;
  toggleSidebar: () => void;
  resetWorkspace: () => void;
}

/**
 * Client UI & workspace store (Zustand).
 *
 * Security note: NEVER store authentication tokens, session secrets, or raw
 * credentials here. Auth sessions are persisted strictly in HttpOnly cookies
 * and hydrated from GET /api/v1/auth/me via TanStack Query.
 */
export const useWorkspaceStore = create<WorkspaceUiState>()(
  persist(
    (set) => ({
      selectedMembershipId: null,
      selectedChildId: null,
      sidebarCollapsed: false,
      setSelectedMembershipId: (id) => set({ selectedMembershipId: id }),
      setSelectedChildId: (id) => set({ selectedChildId: id }),
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      resetWorkspace: () =>
        set({ selectedMembershipId: null, selectedChildId: null }),
    }),
    {
      name: "lms-workspace-ui",
      storage: createJSONStorage(() => sessionStorage),
    }
  )
);

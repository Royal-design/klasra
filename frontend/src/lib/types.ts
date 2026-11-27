export type SchoolRole = "school_admin" | "teacher" | "student" | "parent";

export interface MembershipSummary {
  id: string;
  school_id: string;
  school_name: string | null;
  school_slug: string | null;
  role: SchoolRole | string;
  status: "pending" | "active" | "revoked" | string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_platform_admin: boolean;
  is_active: boolean;
  memberships: MembershipSummary[];
}

export interface LoginResponse {
  user: UserProfile;
  csrf_token: string;
}

export interface MessageResponse {
  message: string;
}

export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  meta: PaginationMeta;
}

export interface ApiErrorEnvelope {
  error?: {
    code?: string;
    message?: string;
    details?: Array<Record<string, unknown>>;
  };
  detail?: string | Array<{ msg?: string; loc?: Array<string | number> }>;
}

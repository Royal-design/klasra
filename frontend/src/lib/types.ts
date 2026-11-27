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

/* --- Phase 3: Platform Admin & School Admin Domain Types --- */

export interface School {
  id: string;
  name: string;
  slug: string;
  status: "active" | "suspended" | string;
  terminology_config: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface SchoolUser {
  membership_id: string;
  school_id: string;
  user_id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  role: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AcademicYear {
  id: string;
  school_id: string;
  name: string;
  start_date: string;
  end_date: string;
  status: string;
  created_at: string;
}

export interface Term {
  id: string;
  school_id: string;
  academic_year_id: string;
  academic_year_name: string | null;
  name: string;
  start_date: string;
  end_date: string;
}

export interface YearLevel {
  id: string;
  school_id: string;
  name: string;
  display_order: number;
}

export interface ClassGroup {
  id: string;
  school_id: string;
  academic_year_id: string;
  academic_year_name: string | null;
  year_level_id: string;
  year_level_name: string | null;
  name: string;
}

export interface Subject {
  id: string;
  school_id: string;
  code: string;
  name: string;
}

export interface OfferingTeacherSummary {
  user_id: string;
  full_name: string;
  email: string;
}

export interface SubjectOffering {
  id: string;
  school_id: string;
  class_group_id: string;
  class_group_name: string | null;
  subject_id: string;
  subject_code: string | null;
  subject_name: string | null;
  term_id: string | null;
  term_name: string | null;
  status: string;
  teacher_user_ids: string[];
  teachers: OfferingTeacherSummary[];
}

export interface Enrollment {
  id: string;
  school_id: string;
  student_user_id: string;
  student_full_name: string | null;
  student_email: string | null;
  academic_year_id: string;
  academic_year_name: string | null;
  class_group_id: string;
  class_group_name: string | null;
  subject_offering_id: string | null;
  subject_name: string | null;
  status: string;
  effective_from: string;
  effective_to: string | null;
}

export interface StaffInvitation {
  id: string;
  school_id: string;
  school_name: string | null;
  email: string;
  full_name: string;
  role: string;
  status: string;
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
}

export interface StudentRegistrationRequest {
  id: string;
  school_id: string;
  user_id: string;
  membership_id: string;
  email: string;
  full_name: string;
  status: string;
  student_reference: string | null;
  decision_notes: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface RegistrationCodeResponse {
  id: string;
  school_id: string;
  invite_type: string;
  code: string;
  label: string | null;
  max_uses: number;
  expires_at: string;
}

export interface GuardianLink {
  id: string;
  school_id: string;
  school_name: string | null;
  student_user_id: string;
  student_full_name: string | null;
  student_email: string | null;
  parent_user_id: string | null;
  guardian_email: string;
  guardian_full_name: string;
  relationship_label: string;
  status: string;
  verified_at: string | null;
  approved_at: string | null;
  revoked_at: string | null;
  decision_notes: string | null;
  created_at: string;
}

export interface ImportRowError {
  row_number: number;
  field: string;
  message: string;
}

export interface ImportValidationResponse {
  total_rows: number;
  valid_rows: number;
  error_count: number;
  errors: ImportRowError[];
}

export interface ImportCommitResponse {
  total_rows: number;
  created_users: number;
  created_memberships: number;
  created_enrollments: number;
}

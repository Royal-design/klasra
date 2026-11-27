import type { ApiErrorEnvelope } from "@/lib/types";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "/api/v1"
).replace(/\/+$/, "");

let inMemoryCsrfToken: string | null = null;

export function setCsrfToken(token: string | null) {
  inMemoryCsrfToken = token;
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const parts = document.cookie.split(";").map((c) => c.trim());
  for (const part of parts) {
    if (part.startsWith(`${name}=`)) {
      return decodeURIComponent(part.slice(name.length + 1));
    }
  }
  return null;
}

export function getCsrfToken(): string | null {
  if (inMemoryCsrfToken) return inMemoryCsrfToken;
  return readCookie("__Host-lms_csrf") || readCookie("lms_csrf");
}

export class ApiClientError extends Error {
  status: number;
  code: string;
  details: Array<Record<string, unknown>>;

  constructor(
    status: number,
    code: string,
    message: string,
    details: Array<Record<string, unknown>> = []
  ) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function extractErrorMessage(
  payload: ApiErrorEnvelope | null,
  status: number
): { code: string; message: string; details: Array<Record<string, unknown>> } {
  if (payload?.error?.message) {
    return {
      code: payload.error.code || `HTTP_${status}`,
      message: payload.error.message,
      details: payload.error.details || [],
    };
  }
  if (typeof payload?.detail === "string") {
    return { code: `HTTP_${status}`, message: payload.detail, details: [] };
  }
  if (Array.isArray(payload?.detail) && payload.detail.length > 0) {
    const first = payload.detail[0];
    const loc = first.loc ? first.loc.slice(1).join(".") : "";
    const msg = first.msg || "Validation failed.";
    return {
      code: "VALIDATION_ERROR",
      message: loc ? `${loc}: ${msg}` : msg,
      details: [],
    };
  }
  if (status === 429) {
    return {
      code: "RATE_LIMITED",
      message: "Too many requests. Please wait a moment and try again.",
      details: [],
    };
  }
  return {
    code: `HTTP_${status}`,
    message: "Something went wrong. Please try again.",
    details: [],
  };
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers);

  const isFormData =
    typeof FormData !== "undefined" && options.body instanceof FormData;
  if (!isFormData && options.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrf = getCsrfToken();
    if (csrf && !headers.has("X-CSRF-Token")) {
      headers.set("X-CSRF-Token", csrf);
    }
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const response = await fetch(`${API_BASE}${normalizedPath}`, {
    ...options,
    method,
    headers,
    credentials: "include",
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  let parsed: unknown = null;
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = null;
    }
  }

  if (!response.ok) {
    const { code, message, details } = extractErrorMessage(
      parsed as ApiErrorEnvelope | null,
      response.status
    );
    throw new ApiClientError(response.status, code, message, details);
  }

  return parsed as T;
}

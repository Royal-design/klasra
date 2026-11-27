"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { KeyRound, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/ui/password-input";
import { ApiClientError, apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { MessageResponse } from "@/lib/types";
import { changePasswordSchema, extractFieldErrors } from "@/lib/validation";

interface ChangePasswordDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ChangePasswordDialog({
  open,
  onOpenChange,
}: ChangePasswordDialogProps) {
  const router = useRouter();
  const { logout } = useAuth();
  const [currentPassword, setCurrentPassword] = React.useState("");
  const [newPassword, setNewPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [fieldErrors, setFieldErrors] = React.useState<Record<string, string>>({});
  const [submitting, setSubmitting] = React.useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = changePasswordSchema.safeParse({
      currentPassword,
      newPassword,
      confirmPassword,
    });
    if (!parsed.success) {
      setFieldErrors(extractFieldErrors(parsed.error));
      return;
    }
    setFieldErrors({});
    setSubmitting(true);
    try {
      await apiRequest<MessageResponse>("/auth/change-password", {
        method: "POST",
        body: JSON.stringify({
          current_password: parsed.data.currentPassword,
          new_password: parsed.data.newPassword,
        }),
      });
      toast.success("Password changed. Please sign in with your new password.");
      onOpenChange(false);
      await logout();
      router.replace("/login");
    } catch (err) {
      toast.error(
        err instanceof ApiClientError
          ? err.message
          : "Could not change password."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Change password</DialogTitle>
          <DialogDescription>
            For security, changing your password signs out active sessions.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} noValidate className="mt-4 space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="cp-current">Current password</Label>
            <PasswordInput
              id="cp-current"
              autoComplete="current-password"
              value={currentPassword}
              hasError={Boolean(fieldErrors.currentPassword)}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
            {fieldErrors.currentPassword && (
              <p className="text-xs text-destructive">
                {fieldErrors.currentPassword}
              </p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cp-new">New password</Label>
            <PasswordInput
              id="cp-new"
              autoComplete="new-password"
              placeholder="At least 12 characters"
              value={newPassword}
              hasError={Boolean(fieldErrors.newPassword)}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            {fieldErrors.newPassword && (
              <p className="text-xs text-destructive">
                {fieldErrors.newPassword}
              </p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cp-confirm">Confirm new password</Label>
            <PasswordInput
              id="cp-confirm"
              autoComplete="new-password"
              placeholder="Re-enter your new password"
              value={confirmPassword}
              hasError={Boolean(fieldErrors.confirmPassword)}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
            {fieldErrors.confirmPassword && (
              <p className="text-xs text-destructive">
                {fieldErrors.confirmPassword}
              </p>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <KeyRound className="h-4 w-4" />
                  Update Password
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

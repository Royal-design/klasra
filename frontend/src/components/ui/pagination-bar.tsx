import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { PaginationMeta } from "@/lib/types";

interface PaginationBarProps {
  meta?: PaginationMeta;
  onPageChange: (page: number) => void;
}

export function PaginationBar({ meta, onPageChange }: PaginationBarProps) {
  if (!meta || meta.total_pages <= 1) return null;

  return (
    <div className="flex items-center justify-between border-t border-border pt-4 text-xs text-muted-foreground">
      <p>
        Page <strong className="text-foreground">{meta.page}</strong> of{" "}
        <strong className="text-foreground">{meta.total_pages}</strong> (
        {meta.total} total)
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={!meta.has_prev}
          onClick={() => onPageChange(meta.page - 1)}
        >
          <ChevronLeft className="h-3.5 w-3.5" />
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={!meta.has_next}
          onClick={() => onPageChange(meta.page + 1)}
        >
          Next
          <ChevronRight className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}

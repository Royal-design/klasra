import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { KlasraMark } from "@/components/brand/klasra-logo";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 text-center">
      <KlasraMark className="mb-5 h-11 w-11" />
      <p className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        404 · Page Not Found
      </p>
      <h1 className="mt-2 font-display text-2xl font-bold tracking-tight text-foreground">
        This page could not be found
      </h1>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">
        The link may have moved or you may not have access to this page in Klasra.
      </p>
      <div className="mt-6 flex items-center gap-3">
        <Button asChild>
          <Link href="/">
            <ArrowLeft className="h-4 w-4" />
            Back to Home
          </Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="/login">Sign In</Link>
        </Button>
      </div>
    </div>
  );
}

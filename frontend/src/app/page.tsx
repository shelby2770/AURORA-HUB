"use client";

import { useQuery } from "@tanstack/react-query";
import { GraduationCap, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { getHealth, API_BASE_URL } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Home() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: false,
  });

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-6 p-6">
      <div className="flex flex-col items-center gap-2 text-center">
        <GraduationCap className="size-12 text-primary" />
        <h1 className="text-3xl font-bold tracking-tight">Aurora Hub</h1>
        <p className="text-sm text-muted-foreground">
          CS MCQ practice — DU MSc admission prep
        </p>
      </div>

      <Card className="w-full">
        <CardHeader>
          <CardTitle>Backend connection</CardTitle>
          <CardDescription className="break-all">{API_BASE_URL}</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-2 text-sm">
          {health.isLoading && (
            <>
              <Loader2 className="size-4 animate-spin" /> Checking…
            </>
          )}
          {health.isError && (
            <>
              <XCircle className="size-4 text-destructive" /> Backend unreachable
            </>
          )}
          {health.isSuccess && (
            <>
              <CheckCircle2 className="size-4 text-emerald-500" />{" "}
              {health.data.service} · {health.data.status}
            </>
          )}
        </CardContent>
      </Card>

      <Button
        className="w-full"
        size="lg"
        onClick={() => toast.success("Phase 0 scaffold is live")}
      >
        Test toast
      </Button>

      <p className="text-xs text-muted-foreground">
        Phase 0 · scaffold &amp; contracts
      </p>
    </main>
  );
}

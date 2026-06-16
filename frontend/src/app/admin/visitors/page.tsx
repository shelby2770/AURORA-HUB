"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Globe, Lock, MapPin, RotateCcw, Users } from "lucide-react";
import {
  ApiError,
  getVisitStats,
  getVisits,
  type CountryStat,
  type Visit,
} from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";

const PW_KEY = "aurora_admin_pw";

/** ISO 3166-1 alpha-2 code → flag emoji (regional indicator letters). */
function flag(code: string | null): string {
  if (!code || code.length !== 2) return "🌐";
  const base = 0x1f1e6;
  return String.fromCodePoint(
    ...[...code.toUpperCase()].map((c) => base + (c.charCodeAt(0) - 65)),
  );
}

function place(geo: Visit["geo"]): string {
  if (!geo) return "—";
  return [geo.city, geo.region, geo.country].filter(Boolean).join(", ") || "—";
}

/** Always render in Bangladesh time (GMT+6), regardless of the viewer's device. */
function bdt(iso: string): string {
  return (
    new Date(iso).toLocaleString("en-GB", {
      timeZone: "Asia/Dhaka",
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    }) + " BDT"
  );
}

function mapsUrl(lat: number, lon: number): string {
  return `https://www.google.com/maps?q=${lat},${lon}`;
}

function isUnauthorized(err: unknown): boolean {
  return err instanceof ApiError && err.status === 401;
}

export default function VisitorsPage() {
  // Password persists for the browser session only; never written to the repo.
  const [password, setPassword] = useState<string>(() =>
    typeof window === "undefined"
      ? ""
      : (sessionStorage.getItem(PW_KEY) ?? ""),
  );

  if (!password) {
    return <Gate onUnlock={setPassword} />;
  }
  return <Dashboard password={password} onLock={() => setPassword("")} />;
}

function Gate({ onUnlock }: { onUnlock: (pw: string) => void }) {
  const [value, setValue] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const pw = value.trim();
    if (!pw) return;
    sessionStorage.setItem(PW_KEY, pw);
    onUnlock(pw);
  };

  return (
    <main className="mx-auto flex min-h-[60vh] w-full max-w-sm flex-col justify-center px-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock className="size-4" /> Admin access
          </CardTitle>
          <CardDescription>
            Enter the admin password to view visitor analytics.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="flex flex-col gap-3">
            <Label htmlFor="pw">Password</Label>
            <input
              id="pw"
              type="password"
              autoFocus
              value={value}
              onChange={(e) => setValue(e.target.value)}
              className="h-9 rounded-md bg-input/30 px-3 text-sm ring-1 ring-foreground/15 outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <Button type="submit">Unlock</Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}

function Dashboard({
  password,
  onLock,
}: {
  password: string;
  onLock: () => void;
}) {
  const stats = useQuery({
    queryKey: ["visit-stats"],
    queryFn: () => getVisitStats(password),
    retry: false,
  });
  const visits = useQuery({
    queryKey: ["visits"],
    queryFn: () => getVisits(password, 200),
    retry: false,
  });

  // Wrong password → clear it and bounce back to the gate.
  if (isUnauthorized(stats.error) || isUnauthorized(visits.error)) {
    sessionStorage.removeItem(PW_KEY);
    return (
      <main className="mx-auto w-full max-w-sm px-4 py-12 text-center">
        <p className="mb-4 text-sm text-destructive">
          Wrong password. Try again.
        </p>
        <Button onClick={onLock}>Back to login</Button>
      </main>
    );
  }

  const totalVisits = (stats.data ?? []).reduce((n, s) => n + s.count, 0);
  const countries = (stats.data ?? []).filter((s) => s.countryCode).length;

  const refetchAll = () => {
    stats.refetch();
    visits.refetch();
  };

  return (
    <main className="mx-auto w-full max-w-4xl px-4 py-8 sm:py-12">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h1 className="font-heading text-2xl font-semibold">Visitors</h1>
          <p className="text-sm text-muted-foreground">
            Where people visit Aurora Hub from, by IP geolocation.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={refetchAll}>
            <RotateCcw className="size-4" /> Refresh
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              sessionStorage.removeItem(PW_KEY);
              onLock();
            }}
          >
            <Lock className="size-4" /> Lock
          </Button>
        </div>
      </div>

      {/* Summary */}
      <div className="mb-6 grid grid-cols-2 gap-3">
        <Card size="sm">
          <CardHeader>
            <CardDescription className="flex items-center gap-1.5">
              <Users className="size-4" /> Total visits
            </CardDescription>
            <CardTitle className="text-2xl">
              {stats.isLoading ? <Skeleton className="h-7 w-16" /> : totalVisits}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card size="sm">
          <CardHeader>
            <CardDescription className="flex items-center gap-1.5">
              <Globe className="size-4" /> Countries
            </CardDescription>
            <CardTitle className="text-2xl">
              {stats.isLoading ? <Skeleton className="h-7 w-16" /> : countries}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* By country */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>By country</CardTitle>
        </CardHeader>
        <CardContent>
          {stats.isLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : stats.isError ? (
            <p className="text-sm text-destructive">
              Couldn’t load stats. Is the backend reachable?
            </p>
          ) : (stats.data ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No visits yet.</p>
          ) : (
            <ul className="divide-y divide-foreground/10">
              {(stats.data ?? []).map((s: CountryStat, i) => (
                <li
                  key={`${s.countryCode}-${i}`}
                  className="flex items-center justify-between py-2"
                >
                  <span className="flex items-center gap-2">
                    <span className="text-lg">{flag(s.countryCode)}</span>
                    {s.country ?? "Unknown"}
                  </span>
                  <Badge variant="secondary">{s.count}</Badge>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* Recent visits */}
      <Card>
        <CardHeader>
          <CardTitle>Recent visits</CardTitle>
          <CardDescription>Most recent first (up to 200).</CardDescription>
        </CardHeader>
        <CardContent>
          {visits.isLoading ? (
            <Skeleton className="h-40 w-full" />
          ) : visits.isError ? (
            <p className="text-sm text-destructive">Couldn’t load visits.</p>
          ) : (visits.data ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No visits yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-muted-foreground">
                  <tr className="border-b border-foreground/10">
                    <th className="py-2 pr-3 font-medium">When (BDT)</th>
                    <th className="py-2 pr-3 font-medium">Location (approx.)</th>
                    <th className="py-2 pr-3 font-medium">Coordinates</th>
                    <th className="py-2 pr-3 font-medium">IP</th>
                    <th className="py-2 font-medium">Path</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-foreground/5">
                  {(visits.data ?? []).map((v: Visit) => (
                    <tr key={v.id}>
                      <td className="py-2 pr-3 whitespace-nowrap text-muted-foreground">
                        {bdt(v.createdAt)}
                      </td>
                      <td className="py-2 pr-3">
                        <span className="flex items-center gap-1.5">
                          <span>{flag(v.geo?.countryCode ?? null)}</span>
                          <MapPin className="size-3 text-muted-foreground" />
                          {place(v.geo)}
                        </span>
                      </td>
                      <td className="py-2 pr-3 whitespace-nowrap font-mono text-xs">
                        {v.geo?.lat != null && v.geo?.lon != null ? (
                          <a
                            href={mapsUrl(v.geo.lat, v.geo.lon)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary underline-offset-2 hover:underline"
                          >
                            {v.geo.lat.toFixed(4)}, {v.geo.lon.toFixed(4)}
                          </a>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="py-2 pr-3 font-mono text-xs">{v.ip}</td>
                      <td className="py-2 text-muted-foreground">
                        {v.path ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </main>
  );
}

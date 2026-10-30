"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { Severity, StateGraph } from "@/lib/types";
import { cn, fmt } from "@/lib/utils";

export const severityVariant: Record<Severity, "ok" | "warn" | "danger"> = {
  low: "ok",
  medium: "warn",
  high: "danger",
  critical: "danger",
};

export function LogVsState({ preview, originalTokens, graph, stateTokens }: {
  preview: string;
  originalTokens: number;
  graph: StateGraph;
  stateTokens: number;
}) {
  const json = JSON.stringify(graph.state, null, 2);
  const [copied, setCopied] = useState(false);
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card className="min-w-0">
        <CardHeader>
          <CardTitle>Original log</CardTitle>
          <CardDescription>
            <span className="font-mono text-foreground">{fmt(originalTokens)}</span> tokens. Showing the first lines.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="max-h-96 overflow-auto rounded-md bg-muted p-3 font-mono text-xs leading-relaxed text-muted-foreground">
            {preview}
          </pre>
        </CardContent>
      </Card>

      <Card className="min-w-0 border-primary/40">
        <CardHeader className="flex-row items-start justify-between gap-3">
          <div className="flex flex-col gap-1">
            <CardTitle>State graph JSON</CardTitle>
            <CardDescription>
              <span className="font-mono text-primary">{fmt(stateTokens)}</span> tokens. This is what the agent reasons over.
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={async () => {
              await navigator.clipboard.writeText(json);
              setCopied(true);
              setTimeout(() => setCopied(false), 1500);
            }}
          >
            {copied ? <Check className="h-3.5 w-3.5" aria-hidden /> : <Copy className="h-3.5 w-3.5" aria-hidden />}
            {copied ? "Copied" : "Copy JSON"}
          </Button>
        </CardHeader>
        <CardContent>
          <pre className="max-h-96 overflow-auto whitespace-pre-wrap break-words rounded-md bg-muted p-3 font-mono text-xs leading-relaxed">
            {json}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}

export function GraphView({ graph }: { graph: StateGraph }) {
  const root = graph.nodes.find((n) => n.kind === "root_cause");
  const deps = graph.nodes.filter((n) => n.kind === "dependency");
  const effects = graph.nodes.filter((n) => n.kind === "effect");
  const { severity } = graph.state;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div className="flex flex-col gap-1">
          <CardTitle>Dependency chain</CardTitle>
          <CardDescription>How the failure travels from root cause to what users see.</CardDescription>
        </div>
        <Badge variant={severityVariant[severity]}>Severity: {severity}</Badge>
      </CardHeader>
      <CardContent className="space-y-5">
        {root && (
          <div className="rounded-md border border-danger/50 bg-danger/5 p-3">
            <div className="text-xs font-medium text-danger">Root cause</div>
            <div className="mt-0.5 text-sm">{root.label}</div>
          </div>
        )}
        {deps.length > 0 && (
          <ol className="flex flex-wrap items-center gap-y-2 text-sm">
            {deps.map((d, i) => (
              <li key={d.id} className="flex items-center">
                <span className={cn("rounded-md border border-border bg-muted px-2.5 py-1 font-mono text-xs")}>
                  {d.label}
                </span>
                {i < deps.length - 1 && (
                  <span className="mx-2 h-px w-6 bg-foreground/40" aria-label="propagates to" role="img" />
                )}
              </li>
            ))}
          </ol>
        )}
        {effects.length > 0 && (
          <div>
            <div className="mb-1.5 text-xs font-medium text-muted-foreground">Secondary effects</div>
            <ul className="flex flex-wrap gap-2">
              {effects.map((e) => (
                <li key={e.id} className="rounded-sm bg-warn/12 px-2 py-1 text-xs text-warn">
                  {e.label}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

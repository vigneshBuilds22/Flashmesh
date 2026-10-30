"use client";

import { AlertTriangle, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CompressionBars } from "@/components/compression-bars";
import { GroundingPanel } from "@/components/grounding-panel";
import { MetricsDashboard } from "@/components/metrics-dashboard";
import { ReasoningPanel } from "@/components/reasoning-panel";
import { GraphView, LogVsState } from "@/components/state-view";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Workflow } from "@/components/workflow";
import { loadAnalysis } from "@/lib/api";
import type { AnalysisResult } from "@/lib/types";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">{title}</h2>
      {children}
    </section>
  );
}

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    loadAnalysis(id)
      .then((r) => alive && setResult(r))
      .catch((e) => alive && setError(e instanceof Error ? e.message : "Analysis failed"));
    return () => {
      alive = false;
    };
  }, [id]);

  if (error) {
    return (
      <div className="max-w-xl space-y-4">
        <div role="alert" className="flex gap-3 rounded-lg border border-danger/40 bg-danger/10 p-4 text-sm">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-danger" aria-hidden />
          <div>
            <p className="font-medium text-danger">The analysis stopped</p>
            <p className="mt-1 break-words">{error}</p>
          </div>
        </div>
        <Button asChild variant="outline">
          <Link href="/"><ArrowLeft className="h-4 w-4" aria-hidden />Back to upload</Link>
        </Button>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Analyzing your logs</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            This usually takes 10 to 40 seconds. The model runs twice: once to extract state, once to reason.
          </p>
        </div>
        <Workflow running />
      </div>
    );
  }

  const { metrics: m, state_graph: graph } = result;
  return (
    <div className="space-y-12">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold">{result.filename}</h1>
          {result.mock && <Badge variant="warn">Mock data</Badge>}
        </div>
        <Button asChild variant="outline" size="sm">
          <Link href="/"><ArrowLeft className="h-3.5 w-3.5" aria-hidden />Analyze another log</Link>
        </Button>
      </div>

      <div className="rounded-lg border border-border bg-card p-5 sm:p-6">
        <CompressionBars before={m.original_tokens} after={m.state_tokens} />
      </div>

      <Section title="Logs compared with state">
        <LogVsState preview={result.log_preview} originalTokens={m.original_tokens} graph={graph} stateTokens={m.state_tokens} />
        <GraphView graph={graph} />
      </Section>

      <Section title="Grounding">
        <GroundingPanel grounding={result.grounding} />
      </Section>

      <Section title="Reasoning">
        <ReasoningPanel reasoning={result.reasoning} />
      </Section>

      <Section title="Metrics">
        <Workflow latency={m.stage_latency_ms} />
        <MetricsDashboard m={m} />
      </Section>
    </div>
  );
}

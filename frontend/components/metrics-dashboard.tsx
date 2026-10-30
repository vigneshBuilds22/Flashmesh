import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { Metrics } from "@/lib/types";
import { fmt, usd } from "@/lib/utils";

const STAGE_LABEL: Record<string, string> = {
  preprocess: "Preprocess",
  state_extraction: "State extraction",
  state_graph: "State graph",
  grounding: "Grounding",
  reasoning: "Reasoning",
};

function Stat({ label, value, sub, accent }: { label: string; value: string; sub?: string; accent?: boolean }) {
  return (
    <Card>
      <CardContent className="space-y-1 pt-5">
        <div className="text-sm text-muted-foreground">{label}</div>
        <div className={`font-mono text-3xl font-semibold tabular-nums ${accent ? "text-primary" : ""}`}>{value}</div>
        {sub && <div className="text-xs text-muted-foreground">{sub}</div>}
      </CardContent>
    </Card>
  );
}

export function MetricsDashboard({ m }: { m: Metrics }) {
  const entries = Object.entries(m.stage_latency_ms);
  const total = entries.reduce((a, [, v]) => a + v, 0) || 1;
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat accent label="Token reduction" value={`${m.reduction_pct}%`} sub={`${fmt(m.tokens_saved)} tokens saved`} />
        <Stat label="Compression" value={`${m.compression_ratio}x`} sub={`${fmt(m.original_tokens)} to ${fmt(m.state_tokens)}`} />
        <Stat accent label="Estimated cost reduction" value={`${m.cost_reduction_pct}%`} sub={`${usd(m.baseline_cost_usd)} to ${usd(m.flashmesh_cost_usd)} per reasoning pass`} />
        <Stat label="Lines deduplicated" value={fmt(m.dedup_lines_removed)} sub="removed before any model call" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Where the time went</CardTitle>
            <CardDescription>Latency per pipeline stage.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5">
            {entries.map(([k, v]) => (
              <div key={k} className="grid grid-cols-[8.5rem_1fr_4.5rem] items-center gap-3 text-sm">
                <span className="text-muted-foreground">{STAGE_LABEL[k] ?? k}</span>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div className="bar-grow h-full bg-primary" style={{ width: `${Math.max((v / total) * 100, 1)}%` }} />
                </div>
                <span className="text-right font-mono text-xs tabular-nums">{v} ms</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>What this run actually cost</CardTitle>
            <CardDescription>Real tokens billed by the model for this analysis.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-baseline justify-between">
              <span className="text-muted-foreground">Tokens billed (extraction + reasoning)</span>
              <span className="font-mono font-semibold tabular-nums">{fmt(m.pipeline_tokens_used)}</span>
            </div>
            <p className="max-w-prose text-xs leading-relaxed text-muted-foreground">
              Extraction is paid once. Every later agent step reads the compact state instead of the raw logs, which is
              where the saving compounds. {m.note}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

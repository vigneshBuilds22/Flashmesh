"use client";

import { AlertTriangle, Loader2, Terminal } from "lucide-react";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fmt } from "@/lib/utils";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface AgentCall {
  tool?: string | null;
  arguments?: Record<string, string | number> | null;
  rationale?: string;
  valid_call: boolean;
  correct: boolean;
  error?: string;
  input_tokens_est?: number;
  tokens_billed?: number;
  latency_ms?: number;
  grounded?: boolean;
  ungrounded_args?: string[];
}
interface Row {
  file: string;
  category: string;
  expected_tool: string;
  raw_tokens: number;
  state_tokens?: number;
  extraction_tokens_billed?: number;
  extraction_latency_ms?: number;
  flashmesh: AgentCall;
  raw_control?: AgentCall;
}
interface Report {
  model: string;
  rows: Row[];
  summary: Record<string, string>;
  complete?: boolean;
}

const sum = (xs: (number | undefined)[]) => xs.reduce<number>((a, b) => a + (b ?? 0), 0);
const pct = (a: number, b: number) => (b > 0 ? Math.round(100 * (1 - a / b)) : 0);

function Stat({ label, a, b, aLabel, bLabel }: { label: string; a: string; b?: string; aLabel: string; bLabel: string }) {
  return (
    <Card>
      <CardContent className="space-y-2 pt-5">
        <div className="text-sm text-muted-foreground">{label}</div>
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-3xl font-semibold tabular-nums text-primary">{a}</span>
          <span className="text-xs text-muted-foreground">{aLabel}</span>
        </div>
        {b !== undefined && (
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-lg tabular-nums">{b}</span>
            <span className="text-xs text-muted-foreground">{bLabel}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function CallCell({ call, tokensIn }: { call?: AgentCall; tokensIn?: number }) {
  if (!call) return <span className="text-muted-foreground">not run</span>;
  if (call.error) return <span className="text-danger">{call.error}</span>;
  const ungrounded = call.ungrounded_args ?? [];
  return (
    <div className="space-y-1.5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-xs font-medium">{call.tool}</span>
        <Badge variant={call.correct ? "ok" : "danger"}>{call.correct ? "right tool" : "wrong tool"}</Badge>
        {call.grounded === false && <Badge variant="warn">invented argument</Badge>}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-0.5 font-mono text-xs text-muted-foreground">
        {Object.entries(call.arguments ?? {}).map(([k, v]) => (
          <span key={k} className={ungrounded.includes(k) ? "text-warn" : ""}>
            {k}={String(v)}
          </span>
        ))}
      </div>
      <div className="text-xs text-muted-foreground">
        reads {fmt(tokensIn ?? call.input_tokens_est ?? 0)} tokens · billed {fmt(call.tokens_billed ?? 0)}
        {call.latency_ms !== undefined && <> · {(call.latency_ms / 1000).toFixed(1)}s</>}
      </div>
    </div>
  );
}

export default function ValidationPage() {
  const [rep, setRep] = useState<Report | null>(null);
  const [error, setError] = useState<{ kind: "missing" | "route" | "other"; msg: string } | null>(null);

  useEffect(() => {
    let alive = true;
    fetch(`${BASE}/api/validation`)
      .then(async (r) => {
        if (r.ok) return (await r.json()) as Report;
        let detail = "";
        try { detail = String((await r.json()).detail ?? ""); } catch {}
        if (r.status === 404 && detail.startsWith("No validation report")) throw { kind: "missing", msg: detail };
        if (r.status === 404) throw { kind: "route", msg: "" };
        throw { kind: "other", msg: `Request failed (${r.status}) ${detail}` };
      })
      .then((d) => alive && setRep(d))
      .catch((e) =>
        alive &&
        setError(e?.kind ? e : { kind: "other", msg: `Cannot reach the FlashMesh API at ${BASE}. Is the backend running?` })
      );
    return () => {
      alive = false;
    };
  }, []);

  if (error?.kind === "missing")
    return (
      <div className="max-w-2xl space-y-3">
        <h1 className="text-2xl font-semibold">No validation report yet</h1>
        <p className="text-sm text-muted-foreground">
          The backend is running but found no report. Run the validation agent from the backend folder and wait for it
          to print each incident as done, then refresh.
        </p>
        <pre className="flex items-center gap-2 rounded-md bg-muted p-3 font-mono text-xs">
          <Terminal className="h-4 w-4 shrink-0" aria-hidden />
          python -m scripts.validate_agent --baseline
        </pre>
        <p className="break-all font-mono text-xs text-muted-foreground">{error.msg.replace("No validation report yet. ", "")}</p>
      </div>
    );
  if (error?.kind === "route")
    return (
      <div role="alert" className="max-w-2xl space-y-2 rounded-lg border border-danger/40 bg-danger/10 p-4 text-sm">
        <p className="font-medium text-danger">The backend has no /api/validation route</p>
        <p>
          It is running older code. Make sure <span className="font-mono">backend/app/routers/validation.py</span> exists
          and <span className="font-mono">backend/app/main.py</span> includes it, then restart the backend.
        </p>
      </div>
    );
  if (error)
    return (
      <div role="alert" className="flex max-w-xl gap-3 rounded-lg border border-danger/40 bg-danger/10 p-4 text-sm">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-danger" aria-hidden />
        {error.msg}
      </div>
    );
  if (!rep)
    return (
      <p className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> Loading report
      </p>
    );

  const rows = rep.rows;
  const hasControl = rows.every((r) => r.raw_control);
  const fmDecision = sum(rows.map((r) => r.flashmesh.tokens_billed));
  const fmExtract = sum(rows.map((r) => r.extraction_tokens_billed));
  const rawBilled = sum(rows.map((r) => r.raw_control?.tokens_billed));
  const rawIn = sum(rows.map((r) => r.raw_tokens));
  const stateIn = sum(rows.map((r) => r.state_tokens));
  const flagged = rows.flatMap((r) =>
    (["flashmesh", "raw_control"] as const)
      .map((k) => ({ r, k, call: r[k] }))
      .filter((x) => x.call?.grounded === false)
  );
  const s = rep.summary;

  return (
    <div className="space-y-10">
      <div className="max-w-3xl space-y-2">
        <h1 className="text-2xl font-semibold">Validation: can an agent act on the compact state?</h1>
        <p className="text-sm leading-relaxed text-muted-foreground">
          For each incident, FlashMesh compresses the raw log into a state, and an agent picks one of four remediation
          tools (simulated, nothing is executed) from that state alone. A second agent gets the full raw log as a
          control. Model: <span className="font-mono text-foreground">{rep.model}</span>
        </p>
        {rep.complete === false && <Badge variant="warn">Partial run: some incidents did not finish</Badge>}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Right tool chosen" a={s.flashmesh_correct} aLabel="from state" b={s.raw_control_correct} bLabel="from raw logs" />
        {s.flashmesh_grounded && (
          <Stat label="Arguments found in the logs" a={s.flashmesh_grounded} aLabel="from state" b={s.raw_control_grounded} bLabel="from raw logs" />
        )}
        <Stat label="Agent input tokens" a={fmt(stateIn)} aLabel="state" b={fmt(rawIn)} bLabel="raw logs" />
        {hasControl && (
          <Stat
            label="Tokens billed, extraction included"
            a={`-${pct(fmDecision + fmExtract, rawBilled)}%`}
            aLabel={`${fmt(fmDecision + fmExtract)} vs ${fmt(rawBilled)}`}
            b={`-${pct(fmDecision, rawBilled)}%`}
            bLabel={`decision only, ${fmt(fmDecision)}`}
          />
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Per incident</CardTitle>
          <CardDescription>Same agent, same prompt. Only what it reads differs.</CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-left text-sm">
            <thead className="text-xs text-muted-foreground">
              <tr className="border-b border-border">
                <th className="pb-2 pr-4 font-medium">Incident</th>
                <th className="pb-2 pr-4 font-medium">Reads</th>
                <th className="pb-2 pr-4 font-medium">Agent reading the state</th>
                <th className="pb-2 font-medium">Agent reading the raw logs</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.file} className="border-b border-border align-top last:border-0">
                  <td className="py-4 pr-4">
                    <div className="font-medium">{r.category}</div>
                    <div className="font-mono text-xs text-muted-foreground">{r.file}</div>
                    <div className="mt-1 text-xs text-muted-foreground">expects <span className="font-mono">{r.expected_tool}</span></div>
                  </td>
                  <td className="py-4 pr-4 font-mono text-xs tabular-nums">
                    <div>{fmt(r.raw_tokens)} tokens</div>
                    <div className="text-primary">{fmt(r.state_tokens ?? 0)} state</div>
                  </td>
                  <td className="py-4 pr-4"><CallCell call={r.flashmesh} tokensIn={r.state_tokens} /></td>
                  <td className="py-4"><CallCell call={r.raw_control} tokensIn={r.raw_tokens} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {flagged.length > 0 && (
        <Card className="border-warn/50">
          <CardHeader>
            <CardTitle>Where the state lost something</CardTitle>
            <CardDescription>The tool was right, but an argument does not appear in the original log.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm leading-relaxed">
            {flagged.map(({ r, k, call }) => (
              <p key={r.file + k}>
                <span className="font-medium">{r.category}</span> ({k === "flashmesh" ? "state" : "raw logs"}):{" "}
                {(call?.ungrounded_args ?? []).map((a) => (
                  <span key={a} className="mr-2 font-mono text-warn">{a}={String(call?.arguments?.[a])}</span>
                ))}
                is not in the log, so a real tool call would fail or hit the wrong target.
              </p>
            ))}
            <p className="text-muted-foreground">
              Fix: have extraction keep concrete identifiers (service names, current and previous versions) alongside
              the diagnosis.
            </p>
          </CardContent>
        </Card>
      )}

      <p className="max-w-3xl text-xs leading-relaxed text-muted-foreground">
        {rows.length} incidents, one run each. This shows the state preserved enough to pick the right action, not that
        it is better than raw logs. Extraction is a one-time cost per incident; later steps read the state only.
      </p>
    </div>
  );
}

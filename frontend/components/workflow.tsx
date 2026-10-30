import { Check, ChevronDown, ChevronRight, Loader2 } from "lucide-react";
import { Fragment } from "react";
import { cn } from "@/lib/utils";

const STAGES = [
  { key: "preprocess", label: "Raw Logs", hint: "Upload and dedupe" },
  { key: "state_extraction", label: "State Extraction", hint: "Nemotron to JSON" },
  { key: "state_graph", label: "State Graph", hint: "Root cause to effects" },
  { key: "grounding", label: "Grounding", hint: "Tavily search" },
  { key: "reasoning", label: "Reasoning", hint: "Nemotron analysis" },
  { key: "fix", label: "Fix", hint: "Remediation plan" },
] as const;

interface Props {
  latency?: Record<string, number>;
  running?: boolean;
}

export function Workflow({ latency, running }: Props) {
  const done = !!latency;
  return (
    <ol className="flex flex-col items-stretch gap-1 md:flex-row md:items-center md:gap-0">
      {STAGES.map((s, i) => {
        const ms = latency?.[s.key];
        return (
          <Fragment key={s.key}>
            <li
              className={cn(
                "flex flex-1 items-center justify-between gap-3 rounded-md border px-3 py-2.5 md:flex-col md:items-start md:justify-start md:gap-1",
                done ? "border-ok/40 bg-ok/5" : running ? "border-primary/40 bg-primary/5" : "border-border bg-card"
              )}
            >
              <div className="flex items-center gap-1.5 text-sm font-medium">
                {done ? (
                  <Check className="h-3.5 w-3.5 text-ok" aria-hidden />
                ) : running ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" aria-hidden />
                ) : null}
                {s.label}
              </div>
              <div className="text-xs text-muted-foreground">
                {s.hint}
                {ms !== undefined && <span className="ml-1.5 font-mono text-foreground">{ms} ms</span>}
              </div>
            </li>
            {i < STAGES.length - 1 && (
              <>
                <ChevronDown className="mx-auto h-4 w-4 shrink-0 text-muted-foreground md:hidden" aria-hidden />
                <ChevronRight className="hidden h-4 w-4 shrink-0 text-muted-foreground md:block" aria-hidden />
              </>
            )}
          </Fragment>
        );
      })}
    </ol>
  );
}

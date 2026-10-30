import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { Reasoning } from "@/lib/types";

export function ReasoningPanel({ reasoning }: { reasoning: Reasoning }) {
  const conf = Math.round(reasoning.confidence_score * 100);
  const tone = conf >= 75 ? "bg-ok" : conf >= 50 ? "bg-warn" : "bg-danger";
  return (
    <div className="grid gap-4 lg:grid-cols-5">
      <Card className="lg:col-span-3">
        <CardHeader>
          <CardTitle>Root cause analysis</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <p className="max-w-prose text-sm leading-relaxed">{reasoning.root_cause_analysis}</p>
          <div>
            <h4 className="mb-2 text-sm font-semibold">Remediation plan</h4>
            <ol className="list-decimal space-y-1.5 pl-5 text-sm leading-relaxed marker:text-muted-foreground">
              {reasoning.remediation_plan.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ol>
          </div>
        </CardContent>
      </Card>

      <div className="flex flex-col gap-4 lg:col-span-2">
        <Card className="border-primary/40">
          <CardHeader>
            <CardTitle>Recommended fix</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap break-words rounded-md bg-muted p-3 font-mono text-xs leading-relaxed">
              {reasoning.fix_recommendation}
            </pre>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Confidence</CardTitle>
            <CardDescription>Model-reported, based on the strength of the evidence.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted" role="presentation">
                <div className={`bar-grow h-full ${tone}`} style={{ width: `${conf}%` }} />
              </div>
              <span className="font-mono text-lg font-semibold tabular-nums">{conf}%</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

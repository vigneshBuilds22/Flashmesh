import { fmt } from "@/lib/utils";

interface Props {
  before: number;
  after: number;
  beforeLabel?: string;
  afterLabel?: string;
}

/** Two bars on the same scale. The width gap IS the product. */
export function CompressionBars({
  before,
  after,
  beforeLabel = "Raw logs",
  afterLabel = "State representation",
}: Props) {
  const pct = before > 0 ? Math.max((after / before) * 100, 0.8) : 0;
  const ratio = after > 0 ? before / after : 0;
  return (
    <div className="space-y-5" role="img" aria-label={`${fmt(before)} tokens compressed to ${fmt(after)} tokens`}>
      <div>
        <div className="mb-1.5 flex items-baseline justify-between gap-4">
          <span className="text-sm text-muted-foreground">{beforeLabel}</span>
          <span className="font-mono text-2xl font-semibold tabular-nums sm:text-3xl">{fmt(before)} tokens</span>
        </div>
        <div className="h-11 w-full rounded-sm border border-border bg-card">
          <div className="noise h-full w-full rounded-sm" />
        </div>
      </div>
      <div>
        <div className="mb-1.5 flex items-baseline justify-between gap-4">
          <span className="text-sm text-muted-foreground">{afterLabel}</span>
          <span className="font-mono text-2xl font-semibold tabular-nums text-primary sm:text-3xl">
            {fmt(after)} tokens
          </span>
        </div>
        <div className="h-11 w-full rounded-sm border border-border bg-card">
          <div className="bar-grow h-full rounded-sm bg-primary" style={{ width: `${pct}%` }} />
        </div>
      </div>
      {ratio > 1 && (
        <p className="text-sm text-muted-foreground">
          <span className="font-semibold text-foreground">{ratio.toFixed(ratio >= 100 ? 0 : 1)}x smaller</span>, same
          incident, one bar scale.
        </p>
      )}
    </div>
  );
}

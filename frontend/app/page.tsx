import { CompressionBars } from "@/components/compression-bars";
import { UploadZone } from "@/components/upload-zone";
import { Workflow } from "@/components/workflow";

export default function Home() {
  return (
    <div className="space-y-14">
      <section className="grid gap-10 lg:grid-cols-2 lg:items-center">
        <div className="space-y-5">
          <h1 className="max-w-xl text-4xl font-semibold leading-[1.1] tracking-tight sm:text-5xl">
            Your agent shouldn&apos;t read 28,000 tokens of logs to find one error.
          </h1>
          <p className="max-w-prose text-base leading-relaxed text-muted-foreground">
            FlashMesh turns raw infrastructure logs into a compact state graph, grounds it with live search, and only
            then lets the model reason. Fewer tokens in, lower cost, faster answers, sharper diagnosis.
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-5 sm:p-6">
          <p className="mb-4 text-sm text-muted-foreground">Demo incident: Redis OOM cascade on Kubernetes</p>
          <CompressionBars before={28000} after={1500} />
        </div>
      </section>

      <section className="max-w-2xl space-y-3">
        <h2 className="text-xl font-semibold">Analyze your own logs</h2>
        <UploadZone />
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">What happens to a log</h2>
        <Workflow />
      </section>
    </div>
  );
}

"use client";

import { FileText, Loader2, Upload } from "lucide-react";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { uploadFile, loadSample } from "@/lib/api";
import { cn, fmt } from "@/lib/utils";

export function UploadZone() {
  const router = useRouter();
  const input = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(label: string, task: () => ReturnType<typeof uploadFile>) {
    setError(null);
    setBusy(label);
    try {
      const info = await task();
      router.push(`/analysis/${info.upload_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
      setBusy(null);
    }
  }

  const onFile = (f?: File) => f && run(f.name, () => uploadFile(f));

  return (
    <div className="space-y-3">
      <div
        role="button"
        tabIndex={0}
        onClick={() => input.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && input.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); onFile(e.dataTransfer.files[0]); }}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors",
          drag ? "border-primary bg-primary/5" : "border-border bg-card hover:border-primary/60"
        )}
      >
        {busy ? (
          <>
            <Loader2 className="h-6 w-6 animate-spin text-primary" aria-hidden />
            <p className="text-sm">Reading {busy}</p>
          </>
        ) : (
          <>
            <Upload className="h-6 w-6 text-primary" aria-hidden />
            <p className="font-medium">Drop a log file here, or click to choose one</p>
            <p className="text-sm text-muted-foreground">
              Kubernetes, Docker, Redis or Python traces. .log or .txt, up to 10 MB.
            </p>
          </>
        )}
        <input
          ref={input}
          type="file"
          accept=".log,.txt,.out,text/plain"
          className="sr-only"
          onChange={(e) => onFile(e.target.files?.[0])}
        />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Button variant="outline" disabled={!!busy} onClick={() => run("demo log", () => loadSample())}>
          <FileText className="h-4 w-4" aria-hidden />
          Analyze the demo incident
        </Button>
        <span className="text-sm text-muted-foreground">Redis OOM cascade, about {fmt(30000)} tokens of logs</span>
      </div>

      {error && (
        <p role="alert" className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
          {error}
        </p>
      )}
    </div>
  );
}

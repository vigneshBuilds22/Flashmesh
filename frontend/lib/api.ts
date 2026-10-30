import type { AnalysisResult, UploadInfo } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function parse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {}
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

async function call(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(`${BASE}${path}`, init);
  } catch {
    throw new Error(`Cannot reach the FlashMesh API at ${BASE}. Is the backend running?`);
  }
}

export async function uploadFile(file: File): Promise<UploadInfo> {
  const form = new FormData();
  form.append("file", file);
  return parse(await call("/api/upload", { method: "POST", body: form }));
}

export async function loadSample(name = "k8s_redis_oom.log"): Promise<UploadInfo> {
  return parse(await call(`/api/samples/${encodeURIComponent(name)}`, { method: "POST" }));
}

// De-duplicates in-flight analyses so React StrictMode's double effect doesn't bill the model twice.
const inflight = new Map<string, Promise<AnalysisResult>>();

export function loadAnalysis(id: string): Promise<AnalysisResult> {
  const existing = inflight.get(id);
  if (existing) return existing;
  const p = (async () => {
    const cached = await call(`/api/results/${id}`);
    if (cached.ok) return (await cached.json()) as AnalysisResult;
    return parse<AnalysisResult>(await call(`/api/analyze/${id}`, { method: "POST" }));
  })();
  inflight.set(id, p);
  p.catch(() => inflight.delete(id));
  return p;
}

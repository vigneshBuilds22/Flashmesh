import { ExternalLink } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { Grounding } from "@/lib/types";

const host = (u: string) => {
  try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return u; }
};

export function GroundingPanel({ grounding }: { grounding: Grounding }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Grounding</CardTitle>
        <CardDescription>
          Searched {grounding.provider} for <span className="font-mono text-foreground">{grounding.query}</span>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {grounding.answer && (
          <p className="max-w-prose rounded-md bg-primary/5 p-3 text-sm leading-relaxed">{grounding.answer}</p>
        )}
        {grounding.results.length === 0 ? (
          <p className="text-sm text-muted-foreground">No search results came back for this query.</p>
        ) : (
          <ul className="grid gap-3 md:grid-cols-2">
            {grounding.results.map((r) => (
              <li key={r.url}>
                <a
                  href={r.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group flex h-full flex-col gap-1 rounded-md border border-border p-3 hover:border-primary/60"
                >
                  <span className="flex items-start justify-between gap-2 text-sm font-medium group-hover:text-primary">
                    {r.title || host(r.url)}
                    <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
                  </span>
                  <span className="font-mono text-xs text-muted-foreground">{host(r.url)}</span>
                  <span className="line-clamp-3 text-xs leading-relaxed text-muted-foreground">{r.snippet}</span>
                </a>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

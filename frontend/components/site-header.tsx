import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-border bg-card">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="grid h-6 w-6 place-items-center rounded-sm bg-primary text-xs font-bold text-primary-foreground">F</span>
          FlashMesh
        </Link>
        <nav className="flex items-center gap-5 text-sm">
          <Link href="/" className="text-muted-foreground hover:text-foreground">Analyze</Link>
          <Link href="/validation" className="text-muted-foreground hover:text-foreground">Validation</Link>
        </nav>
      </div>
    </header>
  );
}

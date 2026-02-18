export function Navbar() {
  return (
    <header className="sticky top-0 z-20 border-b border-white/50 bg-white/70 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-[1680px] items-center justify-between px-4 md:px-6">
        <div className="text-sm uppercase tracking-[0.18em] text-slate-500">mini OpenClaw</div>
        <div className="rounded-full bg-[var(--accent-orange)]/15 px-3 py-1 text-xs font-semibold text-[var(--accent-orange-strong)]">
          Local Transparent Agent
        </div>
      </div>
    </header>
  );
}

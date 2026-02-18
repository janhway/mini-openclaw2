import clsx from "clsx";
import { PropsWithChildren } from "react";

interface PanelProps extends PropsWithChildren {
  className?: string;
}

export function Panel({ children, className }: PanelProps) {
  return (
    <section className={clsx("rounded-2xl border border-white/60 bg-white/65 shadow-[0_16px_40px_-28px_rgba(15,23,42,0.5)] backdrop-blur-md", className)}>
      {children}
    </section>
  );
}

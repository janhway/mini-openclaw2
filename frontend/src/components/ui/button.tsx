import clsx from "clsx";
import { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "ghost" | "outline";
}

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center rounded-xl px-3 py-2 text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60 disabled:cursor-not-allowed disabled:opacity-60",
        variant === "primary" && "bg-[var(--accent-blue)] text-white hover:bg-[var(--accent-blue-strong)]",
        variant === "ghost" && "bg-white/40 text-slate-700 hover:bg-white/60",
        variant === "outline" && "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50",
        className,
      )}
      {...props}
    />
  );
}

import { cn } from "@/lib/utils";

/**
 * Soft filled card used across the FAQ grid and the testimonials grid:
 * a lifted surface, rounded corners, a bold lead line and muted body copy.
 */
export function InfoCard({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-hairline bg-graphite/70 p-6 transition-colors duration-300 hover:border-hairline-strong sm:p-7",
        className
      )}
    >
      {children}
    </div>
  );
}

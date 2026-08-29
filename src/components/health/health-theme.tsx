/** Wraps the HEALTH section in its own light-only palette scope. */
export function HealthThemeScope({ children }: { children: React.ReactNode }) {
  return <div className="health-scope flex min-h-full flex-col">{children}</div>;
}

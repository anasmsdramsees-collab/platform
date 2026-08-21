import { cn } from "@/lib/utils";

export interface Testimonial {
  /** The quote itself. */
  quote: string;
  /** Who said it. */
  name: string;
  /** Their role and company. */
  role: string;
  /** Optional logo path served from /public. */
  logo?: string;
}

interface TestimonialsProps {
  eyebrow: string;
  title: string;
  subtitle?: string;
  testimonials: Testimonial[];
}

function initials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("");
}

function Quote({
  testimonial,
  featured = false,
  className,
}: {
  testimonial: Testimonial;
  featured?: boolean;
  className?: string;
}) {
  return (
    <figure className={cn("flex flex-col justify-between gap-6 bg-void p-6 sm:p-8", className)}>
      <div>
        {testimonial.logo && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={testimonial.logo} alt="" aria-hidden className="mb-5 h-6 w-auto opacity-70" />
        )}
        <blockquote
          className={cn(
            "text-pretty text-chrome-dim",
            featured ? "text-lg leading-relaxed text-platinum sm:text-xl" : "text-sm leading-relaxed sm:text-base"
          )}
        >
          {testimonial.quote}
        </blockquote>
      </div>

      <figcaption className="flex items-center gap-3">
        <span
          aria-hidden
          className="flex size-11 shrink-0 items-center justify-center rounded-full border border-hairline-strong bg-graphite font-mono text-[13px] font-semibold text-ion"
        >
          {initials(testimonial.name)}
        </span>
        <span className="min-w-0">
          <cite className="block truncate text-sm font-semibold not-italic text-platinum">
            {testimonial.name}
          </cite>
          <span className="block truncate text-[12.5px] text-slate">{testimonial.role}</span>
        </span>
      </figcaption>
    </figure>
  );
}

export function Testimonials({ eyebrow, title, subtitle, testimonials }: TestimonialsProps) {
  if (testimonials.length === 0) return null;
  const [featured, ...rest] = testimonials;

  return (
    <section className="border-b border-hairline">
      <div className="mx-auto max-w-6xl px-5 py-20 sm:px-8 sm:py-28">
        <div className="mx-auto max-w-2xl text-center">
          <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">{eyebrow}</p>
          <h2 className="font-display mt-3 text-balance text-3xl font-bold text-platinum sm:text-4xl">
            {title}
          </h2>
          {subtitle && <p className="mt-4 text-chrome-dim">{subtitle}</p>}
        </div>

        {/* Bento grid: the lead quote holds the left column, the rest stack beside it. */}
        <div className="mt-12 grid gap-px overflow-hidden bg-hairline sm:grid-cols-2 lg:grid-cols-4 lg:grid-rows-2">
          <Quote testimonial={featured} featured className="sm:col-span-2 lg:row-span-2" />
          {rest[0] && <Quote testimonial={rest[0]} className="sm:col-span-2" />}
          {rest[1] && <Quote testimonial={rest[1]} />}
          {rest[2] && <Quote testimonial={rest[2]} />}
        </div>
      </div>
    </section>
  );
}

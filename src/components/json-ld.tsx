export default function JsonLd({ data }: { data: Record<string, unknown> }) {
  return (
    <script
      type="application/ld+json"
      // Escape `<` so a "</script>" substring in the data can never close the
      // tag early. Harmless today (data is static config) — a guard for the day
      // any dynamic value reaches this component.
      // eslint-disable-next-line react/no-danger
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }}
    />
  );
}

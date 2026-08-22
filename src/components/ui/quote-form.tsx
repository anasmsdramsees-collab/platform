"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

const LEAD_API = "https://erp.syltraone.com/api/lead";

export interface QuoteCopy {
  name: string;
  phone: string;
  email: string;
  city: string;
  propertyType: string;
  propertyOptions: string[];
  budget: string;
  budgetOptions: string[];
  interests: string;
  interestOptions: string[];
  notes: string;
  submit: string;
  sending: string;
  error: string;
  successTitle: string;
  successBody: string;
  again: string;
  privacy: string;
}

export function QuoteForm({ copy, source = "website" }: { copy: QuoteCopy; source?: string }) {
  const [form, setForm] = React.useState({
    name: "",
    phone: "",
    email: "",
    city: "",
    propertyType: "",
    budget: "",
    notes: "",
    website: "",
  });
  const [interests, setInterests] = React.useState<string[]>([]);
  const [sending, setSending] = React.useState(false);
  const [done, setDone] = React.useState<number | null>(null);
  const [failed, setFailed] = React.useState(false);

  const input =
    "w-full rounded-md border border-hairline bg-void-2 px-3.5 py-2.5 text-sm text-platinum placeholder:text-slate focus:border-hairline-strong focus:outline-none";

  function toggle(item: string) {
    setInterests((prev) =>
      prev.includes(item) ? prev.filter((i) => i !== item) : [...prev, item]
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim() || !form.phone.trim() || sending) return;
    setSending(true);
    setFailed(false);
    try {
      const res = await fetch(LEAD_API, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ ...form, interests, source }),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error();
      setDone(data.lead);
    } catch {
      setFailed(true);
    } finally {
      setSending(false);
    }
  }

  if (done !== null) {
    return (
      <div className="rounded-2xl border border-hairline bg-graphite/70 p-8 text-center sm:p-10">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-ion/15 text-ion">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M20 6 9 17l-5-5" />
          </svg>
        </div>
        <p className="font-display mt-5 text-xl font-bold text-platinum">{copy.successTitle}</p>
        <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-chrome-dim">{copy.successBody}</p>
        <p className="mt-2 font-mono text-xs text-slate">#{done}</p>
        <button
          onClick={() => {
            setDone(null);
            setInterests([]);
            setForm({ name: "", phone: "", email: "", city: "", propertyType: "", budget: "", notes: "", website: "" });
          }}
          className="mt-7 rounded-lg border border-hairline-strong px-5 py-2.5 text-sm font-semibold text-platinum hover:border-ion"
        >
          {copy.again}
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="rounded-2xl border border-hairline bg-graphite/70 p-6 sm:p-8">
      <div className="grid gap-4 sm:grid-cols-2">
        <input
          required
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          placeholder={copy.name}
          className={input}
        />
        <input
          required
          type="tel"
          dir="ltr"
          value={form.phone}
          onChange={(e) => setForm({ ...form, phone: e.target.value })}
          placeholder={copy.phone}
          className={input}
        />
        <input
          type="email"
          dir="ltr"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          placeholder={copy.email}
          className={input}
        />
        <input
          value={form.city}
          onChange={(e) => setForm({ ...form, city: e.target.value })}
          placeholder={copy.city}
          className={input}
        />
        <select
          value={form.propertyType}
          onChange={(e) => setForm({ ...form, propertyType: e.target.value })}
          className={cn(input, !form.propertyType && "text-slate")}
        >
          <option value="">{copy.propertyType}</option>
          {copy.propertyOptions.map((o) => (
            <option key={o} value={o} className="text-platinum">{o}</option>
          ))}
        </select>
        <select
          value={form.budget}
          onChange={(e) => setForm({ ...form, budget: e.target.value })}
          className={cn(input, !form.budget && "text-slate")}
        >
          <option value="">{copy.budget}</option>
          {copy.budgetOptions.map((o) => (
            <option key={o} value={o} className="text-platinum">{o}</option>
          ))}
        </select>
      </div>

      <fieldset className="mt-6">
        <legend className="font-mono text-[11px] uppercase tracking-widest text-slate">
          {copy.interests}
        </legend>
        <div className="mt-3 flex flex-wrap gap-2">
          {copy.interestOptions.map((o) => {
            const active = interests.includes(o);
            return (
              <button
                key={o}
                type="button"
                onClick={() => toggle(o)}
                aria-pressed={active}
                className={cn(
                  "rounded-full border px-3.5 py-1.5 text-[12.5px] transition-colors",
                  active
                    ? "border-ion bg-ion/15 text-ion"
                    : "border-hairline text-chrome-dim hover:border-hairline-strong hover:text-platinum"
                )}
              >
                {o}
              </button>
            );
          })}
        </div>
      </fieldset>

      <textarea
        value={form.notes}
        onChange={(e) => setForm({ ...form, notes: e.target.value })}
        placeholder={copy.notes}
        rows={3}
        className={cn(input, "mt-6")}
      />

      {/* Honeypot */}
      <input
        tabIndex={-1}
        autoComplete="off"
        value={form.website}
        onChange={(e) => setForm({ ...form, website: e.target.value })}
        className="hidden"
        aria-hidden
      />

      {failed && (
        <p className="mt-4 rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-400">{copy.error}</p>
      )}

      <button
        type="submit"
        disabled={sending || !form.name.trim() || !form.phone.trim()}
        className="mt-6 w-full rounded-lg bg-platinum py-3.5 text-sm font-bold text-void transition-opacity hover:opacity-90 disabled:opacity-40"
      >
        {sending ? copy.sending : copy.submit}
      </button>
      <p className="mt-3 text-center text-[11px] leading-relaxed text-slate">{copy.privacy}</p>
    </form>
  );
}

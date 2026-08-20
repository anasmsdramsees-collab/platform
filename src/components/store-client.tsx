"use client";

import { useEffect, useMemo, useState } from "react";
import { productCatalog } from "@/lib/products";
import type { Locale } from "@/lib/i18n/config";

interface CartLine {
  slug: string;
  name: string;
  qty: number;
}

const CART_KEY = "syltra_store_cart";
const ORDER_API = "https://erp.syltraone.com/api/shop-order";

export default function StoreClient({ locale }: { locale: Locale }) {
  const ar = locale === "ar";
  const t = {
    title: ar ? "متجر سيلترا" : "Syltra Store",
    subtitle: ar
      ? "أجهزة المنزل الذكي والأمان والأقفال. أضف ما يناسبك وأرسل طلبك، وفريقنا يتواصل معك لتأكيد السعر والتوصيل والتركيب."
      : "Smart home, security and lock devices. Add what you need and send your order; our team will contact you to confirm pricing, delivery and installation.",
    all: ar ? "الكل" : "All",
    add: ar ? "أضف للسلة" : "Add to cart",
    added: ar ? "في السلة" : "In cart",
    cart: ar ? "سلة الطلب" : "Your order",
    empty: ar ? "السلة فارغة. اضغط على أي جهاز لإضافته." : "Cart is empty. Tap any device to add it.",
    checkout: ar ? "إتمام الطلب" : "Checkout",
    name: ar ? "الاسم الكامل *" : "Full name *",
    phone: ar ? "رقم الجوال *" : "Phone number *",
    city: ar ? "المدينة" : "City",
    address: ar ? "العنوان" : "Address",
    notes: ar ? "ملاحظات (اختياري)" : "Notes (optional)",
    send: ar ? "إرسال الطلب" : "Send order",
    sending: ar ? "جارٍ الإرسال..." : "Sending...",
    priceNote: ar
      ? "الأسعار تؤكد عند التواصل، ويشمل العرض التوصيل والتركيب داخل الرياض."
      : "Pricing is confirmed when we contact you; delivery and installation in Riyadh included in the quote.",
    successTitle: ar ? "استلمنا طلبك" : "Order received",
    successBody: ar
      ? "شكرًا لك! فريق سيلترا سيتواصل معك خلال ساعات العمل لتأكيد الطلب والسعر."
      : "Thank you! The Syltra team will contact you during working hours to confirm your order and pricing.",
    newOrder: ar ? "طلب جديد" : "New order",
    error: ar ? "تعذر إرسال الطلب، حاول مرة أخرى." : "Could not send the order, please try again.",
  };

  const [category, setCategory] = useState("all");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [form, setForm] = useState({ name: "", phone: "", city: "", address: "", notes: "" });
  const [sending, setSending] = useState(false);
  const [done, setDone] = useState<number | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(CART_KEY);
      if (saved) setCart(JSON.parse(saved));
    } catch {
      /* ignore */
    }
  }, []);
  useEffect(() => {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
  }, [cart]);

  const categories = useMemo(
    () => productCatalog.map((c) => ({ key: c.key, name: ar ? c.ar.name : c.en.name })),
    [ar]
  );
  const visible = productCatalog.filter((c) => category === "all" || c.key === category);

  function add(slug: string, name: string, delta: number) {
    setCart((prev) => {
      const next = [...prev];
      const i = next.findIndex((l) => l.slug === slug);
      if (i === -1) {
        if (delta > 0) next.push({ slug, name, qty: delta });
      } else {
        next[i] = { ...next[i], qty: next[i].qty + delta };
        if (next[i].qty <= 0) next.splice(i, 1);
      }
      return next;
    });
  }
  const inCart = (slug: string) => cart.find((l) => l.slug === slug)?.qty ?? 0;
  const totalQty = cart.reduce((s, l) => s + l.qty, 0);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim() || !form.phone.trim() || cart.length === 0 || sending) return;
    setSending(true);
    setError(false);
    try {
      const res = await fetch(ORDER_API, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ ...form, items: cart }),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error();
      setDone(data.order);
      setCart([]);
    } catch {
      setError(true);
    } finally {
      setSending(false);
    }
  }

  if (done !== null) {
    return (
      <div className="mx-auto max-w-xl px-6 py-24 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-ion/15 text-ion">
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M20 6 9 17l-5-5" />
          </svg>
        </div>
        <h1 className="mt-6 font-display text-2xl font-bold text-platinum">{t.successTitle}</h1>
        <p className="mt-3 text-sm leading-relaxed text-chrome-dim">{t.successBody}</p>
        <p className="mt-2 font-mono text-xs text-slate">#{done}</p>
        <button
          onClick={() => setDone(null)}
          className="mt-8 rounded-lg bg-platinum px-6 py-3 text-sm font-bold text-void"
        >
          {t.newOrder}
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 pb-24 pt-14">
      <h1 className="font-display text-3xl font-bold text-platinum sm:text-4xl">{t.title}</h1>
      <p className="mt-3 max-w-2xl text-sm leading-relaxed text-chrome-dim">{t.subtitle}</p>

      {/* Category filter */}
      <div className="mt-8 flex flex-wrap gap-2">
        {[{ key: "all", name: t.all }, ...categories].map((c) => (
          <button
            key={c.key}
            onClick={() => setCategory(c.key)}
            className={`rounded-full border px-4 py-1.5 text-xs font-semibold transition-colors ${
              category === c.key
                ? "border-ion bg-ion/15 text-ion"
                : "border-hairline text-slate hover:text-platinum"
            }`}
          >
            {c.name}
          </button>
        ))}
      </div>

      <div className="mt-10 grid grid-cols-1 gap-10 lg:grid-cols-3">
        {/* Products */}
        <div className="space-y-10 lg:col-span-2">
          {visible.map((cat) => (
            <section key={cat.key}>
              <h2 className="font-display text-lg font-bold text-platinum">{ar ? cat.ar.name : cat.en.name}</h2>
              <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                {cat.items.map((p) => {
                  const qty = inCart(p.slug);
                  const copy = ar ? p.ar : p.en;
                  return (
                    <div key={p.slug} className="rounded-lg border border-hairline bg-graphite p-5">
                      <p className="font-mono text-sm font-semibold text-platinum">{p.name}</p>
                      <p className="mt-1.5 text-xs leading-relaxed text-chrome-dim">{copy.tagline}</p>
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {p.tags.map((tag) => (
                          <span key={tag} className="rounded bg-void-2 px-1.5 py-0.5 font-mono text-[10px] text-slate">
                            {tag}
                          </span>
                        ))}
                      </div>
                      <div className="mt-4">
                        {qty === 0 ? (
                          <button
                            onClick={() => add(p.slug, p.name, 1)}
                            className="w-full rounded-lg border border-ion/50 py-2 text-xs font-bold text-ion transition-colors hover:bg-ion/10"
                          >
                            {t.add}
                          </button>
                        ) : (
                          <div className="flex items-center justify-between rounded-lg bg-ion/10 px-3 py-1.5">
                            <button onClick={() => add(p.slug, p.name, -1)} className="px-2 text-lg font-bold text-ion">-</button>
                            <span className="text-sm font-bold text-ion">{qty}</span>
                            <button onClick={() => add(p.slug, p.name, 1)} className="px-2 text-lg font-bold text-ion">+</button>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          ))}
        </div>

        {/* Cart + checkout */}
        <aside className="h-fit rounded-lg border border-hairline bg-graphite p-6 lg:sticky lg:top-24">
          <h2 className="font-display text-lg font-bold text-platinum">
            {t.cart} {totalQty > 0 && <span className="text-ion">({totalQty})</span>}
          </h2>
          {cart.length === 0 ? (
            <p className="mt-4 text-xs leading-relaxed text-slate">{t.empty}</p>
          ) : (
            <ul className="mt-4 space-y-2">
              {cart.map((l) => (
                <li key={l.slug} className="flex items-center justify-between gap-2 text-xs text-chrome-dim">
                  <span>{l.name}</span>
                  <span className="flex items-center gap-2">
                    <button onClick={() => add(l.slug, l.name, -1)} className="text-slate hover:text-platinum">-</button>
                    <span className="w-5 text-center font-bold text-platinum">{l.qty}</span>
                    <button onClick={() => add(l.slug, l.name, 1)} className="text-slate hover:text-platinum">+</button>
                  </span>
                </li>
              ))}
            </ul>
          )}

          <form onSubmit={submit} className="mt-6 space-y-3 border-t border-hairline pt-5">
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder={t.name}
              className="w-full rounded-md border border-hairline bg-void-2 px-3 py-2 text-sm text-platinum placeholder:text-slate focus:border-hairline-strong focus:outline-none" />
            <input required value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder={t.phone} dir="ltr"
              className="w-full rounded-md border border-hairline bg-void-2 px-3 py-2 text-sm text-platinum placeholder:text-slate focus:border-hairline-strong focus:outline-none" />
            <input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} placeholder={t.city}
              className="w-full rounded-md border border-hairline bg-void-2 px-3 py-2 text-sm text-platinum placeholder:text-slate focus:border-hairline-strong focus:outline-none" />
            <input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} placeholder={t.address}
              className="w-full rounded-md border border-hairline bg-void-2 px-3 py-2 text-sm text-platinum placeholder:text-slate focus:border-hairline-strong focus:outline-none" />
            <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder={t.notes} rows={2}
              className="w-full rounded-md border border-hairline bg-void-2 px-3 py-2 text-sm text-platinum placeholder:text-slate focus:border-hairline-strong focus:outline-none" />
            {error && <p className="rounded-md bg-red-500/10 px-3 py-2 text-xs text-red-400">{t.error}</p>}
            <button
              type="submit"
              disabled={sending || cart.length === 0 || !form.name.trim() || !form.phone.trim()}
              className="w-full rounded-lg bg-platinum py-3 text-sm font-bold text-void transition-opacity hover:opacity-90 disabled:opacity-40"
            >
              {sending ? t.sending : t.send}
            </button>
            <p className="text-[10.5px] leading-relaxed text-slate">{t.priceNote}</p>
          </form>
        </aside>
      </div>
    </div>
  );
}

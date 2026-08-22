import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/site-config";

// Static export needs these emitted at build time.
export const dynamic = "force-static";

/**
 * Cloudflare prepends its own managed block to this file, which disallows the
 * AI *training* crawlers (GPTBot, ClaudeBot, CCBot, Bytespider, Google-Extended,
 * Applebot-Extended and friends) and sets Content-Signal: ai-train=no.
 *
 * We deliberately do not contradict that. Syltra One wants to be quotable when
 * someone asks an assistant about smart homes in Saudi, so the agents listed
 * here are the ones that fetch a page to answer a live question and cite it.
 * Training-only scrapers stay blocked, so the catalogue and copy are not fed
 * into model training for free.
 */
const ANSWER_ENGINES = [
  "OAI-SearchBot", // ChatGPT search results
  "ChatGPT-User", // a user asking ChatGPT to open the page
  "Claude-SearchBot", // Claude search results
  "Claude-User", // a user asking Claude to open the page
  "PerplexityBot",
  "Perplexity-User",
  "DuckAssistBot",
  "Applebot", // Siri and Spotlight, distinct from Applebot-Extended
  "Bingbot", // powers several assistants as well as Bing
];

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      { userAgent: "*", allow: "/" },
      ...ANSWER_ENGINES.map((userAgent) => ({ userAgent, allow: "/" })),
    ],
    sitemap: `${siteUrl}/sitemap.xml`,
    host: siteUrl,
  };
}

import { NextResponse } from "next/server";
import { buildSylaSystemPrompt } from "@/lib/sina/system-prompt";

export const runtime = "nodejs";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

const MAX_MESSAGES = 20;
const MAX_MESSAGE_LENGTH = 2000;
const ANTHROPIC_URL = "https://api.anthropic.com/v1/messages";
const DEFAULT_MODEL = "claude-haiku-4-5-20251001";

function isChatMessage(value: unknown): value is ChatMessage {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return (
    (v.role === "user" || v.role === "assistant") &&
    typeof v.content === "string" &&
    v.content.trim().length > 0 &&
    v.content.length <= MAX_MESSAGE_LENGTH
  );
}

export async function POST(request: Request) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: "not_configured" },
      { status: 503 }
    );
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "invalid_json" }, { status: 400 });
  }

  const rawMessages = (body as { messages?: unknown })?.messages;
  if (!Array.isArray(rawMessages) || rawMessages.length === 0) {
    return NextResponse.json({ error: "missing_messages" }, { status: 400 });
  }

  const messages = rawMessages.filter(isChatMessage).slice(-MAX_MESSAGES);
  if (messages.length === 0) {
    return NextResponse.json({ error: "missing_messages" }, { status: 400 });
  }

  try {
    const res = await fetch(ANTHROPIC_URL, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: process.env.SINA_MODEL || DEFAULT_MODEL,
        max_tokens: 600,
        system: buildSylaSystemPrompt(),
        messages: messages.map((m) => ({ role: m.role, content: m.content })),
      }),
    });

    if (!res.ok) {
      const detail = await res.text().catch(() => "");
      console.error("Syla: Anthropic API error", res.status, detail);
      return NextResponse.json({ error: "upstream_error" }, { status: 502 });
    }

    const data = await res.json();
    const reply = Array.isArray(data.content)
      ? data.content
          .filter((block: { type: string }) => block.type === "text")
          .map((block: { text: string }) => block.text)
          .join("\n")
      : "";

    if (!reply) {
      return NextResponse.json({ error: "empty_reply" }, { status: 502 });
    }

    return NextResponse.json({ reply });
  } catch (err) {
    console.error("Syla: request failed", err);
    return NextResponse.json({ error: "request_failed" }, { status: 500 });
  }
}

// Cloudflare Pages Function: POST /api/sina
// Serves the Syla assistant on the live site using Workers AI (free tier).
import { buildSylaSystemPrompt } from "../../src/lib/sina/system-prompt";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface Env {
  AI: {
    run(
      model: string,
      options: {
        messages: { role: string; content: string }[];
        max_tokens?: number;
      }
    ): Promise<{ response?: string }>;
  };
}

const MAX_MESSAGES = 20;
const MAX_MESSAGE_LENGTH = 2000;
const MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast";

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

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json" },
  });
}

export const onRequestPost = async (context: {
  request: Request;
  env: Env;
}): Promise<Response> => {
  const { request, env } = context;

  if (!env.AI) return json({ error: "not_configured" }, 503);

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid_json" }, 400);
  }

  const messages = (body as { messages?: unknown })?.messages;
  if (
    !Array.isArray(messages) ||
    messages.length === 0 ||
    messages.length > MAX_MESSAGES ||
    !messages.every(isChatMessage)
  ) {
    return json({ error: "invalid_messages" }, 400);
  }

  try {
    const result = await env.AI.run(MODEL, {
      messages: [
        { role: "system", content: buildSylaSystemPrompt() },
        ...messages.map(({ role, content }) => ({ role, content })),
      ],
      max_tokens: 1024,
    });
    const reply = result?.response?.trim();
    if (!reply) return json({ error: "empty_reply" }, 502);
    return json({ reply });
  } catch {
    return json({ error: "upstream_error" }, 502);
  }
};

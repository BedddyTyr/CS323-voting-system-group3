// supabase/functions/ingest-vote/index.ts
// ----------------------------------------
// Receives vote payloads from edge nodes, validates them, and upserts
// into the Supabase 'votes' table. Upsert on the 'id' primary key
// ensures idempotent behaviour — duplicate submissions are safe.

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
);

const REQUIRED_FIELDS = ["id", "user_id", "poll_id", "choice", "timestamp"];
const VALID_CHOICES   = ["A", "B", "C"];

serve(async (req) => {
  // ── Method guard ──────────────────────────────────────────────────────
  if (req.method !== "POST") {
    return json({ error: "Method Not Allowed" }, 405);
  }

  // ── Parse body ────────────────────────────────────────────────────────
  let vote: Record<string, unknown>;
  try {
    vote = await req.json();
  } catch {
    return json({ error: "Invalid JSON payload" }, 400);
  }

  // ── Validate required fields ──────────────────────────────────────────
  for (const field of REQUIRED_FIELDS) {
    if (vote[field] === undefined || vote[field] === null || vote[field] === "") {
      return json({ error: `Missing or empty field: ${field}` }, 400);
    }
  }

  // ── Validate choice value ─────────────────────────────────────────────
  if (!VALID_CHOICES.includes(vote["choice"] as string)) {
    return json({ error: `Invalid choice. Must be one of: ${VALID_CHOICES.join(", ")}` }, 400);
  }

  // ── Upsert (idempotent write) ─────────────────────────────────────────
  // onConflict: "id" means a second POST with the same id overwrites the
  // existing row rather than throwing a unique-constraint error.
  const { error } = await supabase
    .from("votes")
    .upsert(vote, { onConflict: "id" });

  if (error) {
    console.error("DB upsert error:", error.message);
    return json({ error: error.message }, 500);
  }

  return json({ status: "accepted" }, 200);
});

// ── Helper ────────────────────────────────────────────────────────────────
function json(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
